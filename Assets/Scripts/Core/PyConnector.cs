using System;
using System.Collections;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Text;
using UnityEngine;
using Newtonsoft.Json;

using CartPole.Types;
using CartPole.API;


namespace CartPole.Core
{
    public class PyConnector : MonoBehaviour
    {
        const string IP = "127.0.0.1";
        const int PORT = 80;
        Thread mThread;
        IPAddress localAdd;
        TcpListener listener;
        TcpClient client;
        NetworkStream nwStream;
        bool running = false;

        CartPoleAPI cartPoleAPI;
        UnityMainThreadDispatcher dispatcher;

        // 本当はImplementReqの直前に書いてImplementReqを純粋関数にしたいが、
        // 別スレッドでdispatcher.Enqueue()を用いて呼ぶためreturnを取得できず困る
        object sendData = null;

        void Awake()
        {
            cartPoleAPI = FindObjectOfType<CartPoleAPI>();
            dispatcher = FindObjectOfType<UnityMainThreadDispatcher>();
        }

        void Start()
        {
            ThreadStart ts = new ThreadStart(ConnectPython);
            mThread = new Thread(ts);
            mThread.Start();
        }

        void OnApplicationQuit()
        {
            if (mThread != null)
            {
                running = false;
                mThread.Abort();
            }
        }

        void ConnectPython()
        {
            localAdd = IPAddress.Parse(IP);
            listener = new TcpListener(IPAddress.Any, PORT);
            listener.Start();

            client = listener.AcceptTcpClient();
            Debug.Log("connected to server.");
            nwStream = client.GetStream();

            running = true;

            try
            {
                while (running)
                {
                    DataTypes.RequestJsonFormat req = GetResponse();
                    // get-position, set-positionはメインスレッドからしか呼べないので、メインのキューに入れる
                    dispatcher.Enqueue(() => ImplementReq(req));
                    // sendDataが確実に更新されてから実行するため、こちらもメインのキューに入れる
                    dispatcher.Enqueue(() => SendData(200, sendData));
                }
            }
            catch (SocketException sockE)
            {
                Debug.Log("Failed to send message. Please check connection to server.");
                Debug.Log(sockE.ToString());
                SendData(500, null);
            }
            catch (Exception e)
            {
                Debug.Log(e.ToString());
                // ToDo: BadRequest以外もあるはずなので条件分岐する
                SendData(400, null);
            }
            finally
            {
                Debug.Log("stopping listener...");
                listener.Stop();
                mThread.Abort();
            }
        }

        private object ImplementReq(DataTypes.RequestJsonFormat req)
        {
            if (req.reqType == (int)DataTypes.ReqType.GetObs)
            {
                sendData = cartPoleAPI.GetObs();
            }
            else if (req.reqType == (int)DataTypes.ReqType.GetParams)
            {
                sendData = cartPoleAPI.GetParams();
            }
            else if (req.reqType == (int)DataTypes.ReqType.SetParams)
            {
                cartPoleAPI.SetParams((DataTypes.Params)req.data);
            }
            else if (req.reqType == (int)DataTypes.ReqType.Reset)
            {
                sendData = cartPoleAPI.Reset();
            }
            else if (req.reqType == (int)DataTypes.ReqType.Action)
            {
                sendData = cartPoleAPI.Action((DataTypes.Action)Enum.ToObject(typeof(DataTypes.Action), req.data));
            }
            else if (req.reqType == (int)DataTypes.ReqType.Close)
            {
                Debug.Log("connection close requested.");
                throw new Exception();
            }

            return sendData;
        }

        void SendData(int statusCode, object data)
        {
            DataTypes.ResponseJsonFormat sendData;
            sendData.timestamp = (int)DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000;
            sendData.statusCode = statusCode;
            sendData.data = data;

            string jsonString = JsonConvert.SerializeObject(sendData);
            byte[] bytes;
            bytes = Encoding.UTF8.GetBytes(jsonString);
            nwStream.Write(bytes, 0, bytes.Length);
        }

        DataTypes.RequestJsonFormat GetResponse()
        {
            byte[] buffer = new byte[client.ReceiveBufferSize];
            int bytes = nwStream.Read(buffer, 0, client.ReceiveBufferSize);
            string jsonString = Encoding.UTF8.GetString(buffer, 0, bytes);
            return JsonConvert.DeserializeObject<DataTypes.RequestJsonFormat>(jsonString);
        }
    }
}
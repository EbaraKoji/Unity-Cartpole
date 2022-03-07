using System;
using System.Collections;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Text;
using UnityEngine;
using Newtonsoft.Json;

public class PythonCommunicator : MonoBehaviour
{
    const string IP = "127.0.0.1";
    const int PORT = 80;
    Thread mThread;
    IPAddress localAdd;
    TcpListener listener;
    TcpClient client;
    NetworkStream nwStream;
    bool running = false;

    object receiveData;

    struct SendSample
    {
        public float[][] env;
        public float reward;
        public bool done;
        public object info;
    }

    void Start()
    {
        ThreadStart ts = new ThreadStart(ConnectPython);
        mThread = new Thread(ts);
        mThread.Start();
    }

    void Update()
    {

    }

    string StructJsonString()
    {
        SendSample sendSample = new SendSample();
        sendSample.env = new float[][] {
            new float[] { 0.1f, 0.2f, 0.3f },
            new float[] { 0.4f, 0.5f, 0.6f },
        };
        sendSample.reward = 3.7f;
        sendSample.done = true;
        sendSample.info = null;
        return JsonConvert.SerializeObject(sendSample);
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
                receiveData = ReceiveData();
                Debug.Log(receiveData);
                receiveData = null;

                SendData(StructJsonString());
            }
        }
        catch (SocketException sockE)
        {
            Debug.Log("Failed to send message. Please check connection to server.");
            Debug.Log(sockE.ToString());
        }
        finally
        {
            Debug.Log("stopping listener...");
            listener.Stop();
        }
    }

    void SendData(object data)
    {
        byte[] bytes;
        bytes = Encoding.UTF8.GetBytes((string)data);
        nwStream.Write(bytes, 0, bytes.Length);
    }

    object ReceiveData()
    {
        byte[] buffer = new byte[client.ReceiveBufferSize];
        int bytes = nwStream.Read(buffer, 0, client.ReceiveBufferSize);
        return Encoding.UTF8.GetString(buffer, 0, bytes);
    }
}
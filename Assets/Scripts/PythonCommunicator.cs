using System;
using System.Collections;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Text;
using UnityEngine;

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

    SendType sendType;

    ReceiveType receiveType;
    object receiveData;

    string sendMessage;

    void Start()
    {
        ThreadStart ts = new ThreadStart(ConnectPython);
        mThread = new Thread(ts);
        mThread.Start();
    }

    void Update()
    {

    }

    void SendMessage()
    {
        sendMessage = DateTime.Now.ToString();
        SendData(SendType.String, sendMessage);
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
                receiveData = ReceiveData(receiveType, receiveData);
                Debug.Log(receiveData);
                receiveData = null;

                SendMessage();
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

    void SendData(SendType type, object data)
    {
        if (type == SendType.String)
        {
            byte[] bytes = Encoding.UTF8.GetBytes((string)data);
            nwStream.Write(bytes, 0, bytes.Length);
        }
    }

    object ReceiveData(ReceiveType type, object data)
    {
        byte[] buffer = new byte[client.ReceiveBufferSize];
        if (type == ReceiveType.String)
        {
            int bytes = nwStream.Read(buffer, 0, client.ReceiveBufferSize);
            return Encoding.UTF8.GetString(buffer, 0, bytes);
        }
        return null;
    }

    enum SendType
    {
        String,
        Int,
        Float,
        IntArray,
        FloatArray,
        FloatNdArray,
    }

    enum ReceiveType
    {
        String,
        Int,
        Float,
        IntArray,
        FloatArray,
    }
}
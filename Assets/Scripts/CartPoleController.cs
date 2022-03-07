using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CartPoleController : MonoBehaviour
{
    [SerializeField] Rigidbody cart;
    [SerializeField] Rigidbody pole;
    [SerializeField] float cartForce = 1f;
    [SerializeField] float xThreshold = 1f;
    [SerializeField] float thetaThresholdRadians = 12 * 2 * Mathf.PI / 360;

    struct Env
    {
        public float cartPositionX;
        public float cartVelocityX;
        public float poleAngle;
        public float poleAngularVelocity;
    }
    Env env = new Env();
    float reward;
    bool done;
    object info;

    struct Data
    {
        Env env;
        float reward;
        bool done;
        object info;
    }

    enum Action
    {
        Right = 0,
        Left = 1
    }
    Action action;

    Vector3 initialCartPosition = Vector3.zero;
    Vector3 initialPolePosition = new Vector3(0, 1, 0);
    Vector3 initialPoleRotation = Vector3.zero;


    void Start()
    {
        Reset();
    }

    // Update is called once per frame
    void Update()
    {
        Step(TakeRandomAction());
    }

    void UpdateEnv()
    {
        env.cartPositionX = cart.position.x;
        env.cartVelocityX = cart.velocity.x;
        env.poleAngle = pole.rotation.z;
        env.poleAngularVelocity = pole.angularVelocity.z;
    }

    void Reset()
    {
        cart.position = initialCartPosition;
        cart.velocity = Vector3.zero;
        cart.angularVelocity = Vector3.zero;
        pole.position = initialPolePosition;
        pole.velocity = Vector3.zero;
        pole.angularVelocity = Vector3.zero;
        UpdateEnv();
    }

    (Env, float, bool, object) Step(Action action)
    {
        Vector3 force = new Vector3(cartForce, 0, 0);
        if (action == Action.Left)
        {
            force *= -1;
        }
        pole.AddForce(force);
        UpdateEnv();

        done = env.cartPositionX < -xThreshold ||
            env.cartPositionX > xThreshold ||
            env.poleAngle < -thetaThresholdRadians ||
            env.poleAngle > thetaThresholdRadians;
        if (!done)
        {
            reward = 1f;
        }
        else
        {
            reward = 0f;
            Reset();
        }

        return (env, reward, done, info);
    }

    Action TakeRandomAction()
    {
        return Random.Range(0, 1) > 0.5 ? Action.Right : Action.Left;
    }
}
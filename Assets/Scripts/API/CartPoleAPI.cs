using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using CartPole.Types;

namespace CartPole.API
{
    public class CartPoleAPI : MonoBehaviour
    {
        [SerializeField] Rigidbody cart;
        [SerializeField] Rigidbody pole;
        [SerializeField] float cartForce = 10f;

        [SerializeField] float xThreshold = 2.4f;
        [SerializeField] float thetaThresholdRadians = 12 * 2 * Mathf.PI / 360;

        DataTypes.Action action;

        Vector3 initialCartPosition = Vector3.zero;
        Vector3 initialPolePosition = new Vector3(0, 1, 0);
        Vector3 initialPoleRotation = Vector3.zero;

        public DataTypes.Obs GetObs()
        {
            DataTypes.Obs obs;
            obs.cartPositionX = cart.position.x;
            obs.cartVelocityX = cart.velocity.x;
            obs.poleAngle = pole.rotation.z;
            obs.poleAngularVelocity = pole.angularVelocity.z;

            return obs;
        }

        public DataTypes.Params GetParams()
        {
            DataTypes.Params cartPoleParams = new DataTypes.Params();
            return cartPoleParams;
        }

        public void SetParams(DataTypes.Params cartPoleParams)
        {
            
        }

        public DataTypes.Obs Reset()
        {
            pole.velocity = Vector3.zero;
            pole.angularVelocity = Vector3.zero;
            pole.rotation = Quaternion.identity;
            pole.position = initialPolePosition;
            cart.velocity = Vector3.zero;
            cart.angularVelocity = Vector3.zero;
            cart.position = initialCartPosition;

            return GetObs();
        }

        void TakeAction(DataTypes.Action action)
        {
            Vector3 force = new Vector3(cartForce, 0, 0);
            if (action == DataTypes.Action.Left)
            {
                force *= -1;
            }
            cart.AddForce(force);
        }

        public DataTypes.ActionResult Action(DataTypes.Action action)
        {
            DataTypes.ActionResult actionResult = new DataTypes.ActionResult();

            TakeAction(action);

            actionResult.obs = GetObs();
            bool done = isCollapsed();
            actionResult.reward = done ? 0 : 1;
            actionResult.done = done;

            return actionResult;
        }

        bool isCollapsed()
        {
            return (cart.position.x < -xThreshold ||
                    cart.position.x > xThreshold ||
                    pole.rotation.z < -thetaThresholdRadians ||
                    pole.rotation.z > thetaThresholdRadians);
        }
    }
}
namespace CartPole.Types
{
    public class DataTypes
    {
        public struct Obs
        {
            public float cartPositionX;
            public float cartVelocityX;
            public float poleAngle;
            public float poleAngularVelocity;
        }

        public enum Action
        {
            Right = 0,
            Left = 1,
        }

        public struct ActionResult
        {
            public Obs obs;
            public float reward;
            public bool done;
            public object info;
        }

        public enum ReqType
        {
            GetObs = 0,
            GetParams = 1,
            SetParams = 2,
            Reset = 3,
            Action = 4,
            Close = 5,
        }

        // null許容が気持ち悪いのでなんとかしたい
        public struct RequestJsonFormat
        {
            public int reqType;
            public float timestamp;
            public int statusCode;
            public object? data;
        }

        public struct ResponseJsonFormat
        {
            public float timestamp;
            public int statusCode;
            public object? data;
        }

        public struct Params
        {
            public float waitAfterAction;
        }
    }
}
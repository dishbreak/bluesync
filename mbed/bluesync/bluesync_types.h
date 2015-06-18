union intByteArray {
    uint32_t integer;
    int32_t signed_integer;
    uint8_t byte[4];
};

namespace EventCode {
enum EventCodeEnum {
    ADV_RECV = 0x01,
    SLAVE_MODE = 0x02,
    MASTER_MODE = 0x03,
    GET_STATE = 0x04,
    SET_TIMESTAMP = 0x05,
    OFFSET_RECV = 0x06,
    SET_SENSOR_TIME = 0x07
};
}
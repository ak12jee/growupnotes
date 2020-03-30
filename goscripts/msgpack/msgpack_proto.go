package test

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
	"os"
	"unsafe"

	"github.com/vmihailenco/msgpack"
)

// MsgHeader 注释
type MsgHeader struct {
	BodySize  int16
	Checksum  int16
	Timestamp int32
	MsgID     int32
}

type MsgCo struct {
	MsgId  int32  `msgpack:"msgId"`
	UserId int32  `msgpack:"userId"`
	Data   string `msgpack:"data"`
}

type LMsgC2Stokencheck struct {
	MsgID       int32  `msgpack:"m_msgId"`
	UserId      int32  `msgpack:"m_userId"`
	UccessToken string `msgpack:"m_accessToken"`
}

func Msgpack_marshal_proto() {
	s, _ := msgpack.Marshal(&LMsgC2Stokencheck{
		MsgID:       186003,
		UserId:      1234,
		UccessToken: "fewfw@432afwffqw-fweigf"})

	b, _ := msgpack.Marshal(&MsgCo{
		MsgId:  186003,
		UserId: 2,
		Data:   *(*string)(unsafe.Pointer(&s))})

	var msgHead = MsgHeader{BodySize: int16(len(b)), Checksum: int16(100), Timestamp: 1524551, MsgID: 186001 * (1524551%10000 + 1)}

	buf := new(bytes.Buffer)
	err := binary.Write(buf, binary.LittleEndian, msgHead)
	if err != nil {
		fmt.Println("binary encode failed, err:", err)
		return
	}
	err = binary.Write(buf, binary.LittleEndian, b)
	con, err := net.Dial("tcp", "127.0.0.1:6001")
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	n, err1 := con.Write(buf.Bytes())
	if err1 != nil {
		fmt.Println(err1)
		os.Exit(1)
	}
	fmt.Println("send buff length : ", n)
	defer con.Close()
}

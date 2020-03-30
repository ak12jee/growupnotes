package test

import "testing"

func TestMsgpack_marshal_proto(*testing.T) {
	Msgpack_marshal_proto()
}

func BenchMsgpack_marshal_proto(t *testing.B) {

	for i := 0; i < t.N; i++ {
		Msgpack_marshal_proto()
	}
}

#pragma once

#define macro_get_member_value(argType, arg) \
	argType get_##arg() {\
	return m_##arg;\
	}

#define macro_get_member_value_ref(argType, arg)\
	argType& get_##arg##_ref() {\
	return m_##arg;\
	}

#define macro_set_member_value(argType, arg) \
	void set_##arg(const argType & v){\
	m_##arg = v;\
	}

#define macro_get_set_member_value(argType, arg) \
	macro_get_member_value(argType, arg) \
	macro_set_member_value(argType, arg)

#define tostr(x) #x
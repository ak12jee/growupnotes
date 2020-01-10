
# -*- coding: UTF-8 -*-

import platform
import os
import sys
import shutil
import time
import subprocess

if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

if 'Windows' in platform.platform():
    compiler = "Visual Studio 14 2015"
elif 'Linux' in platform.platform():
    compiler = "Unix Makefiles"

CFG_CURRENTWORK_DIR = '.'
CFG_BUILD_TYPE = 'Debug'
CFG_BUILD_BINARY_DIR = '.build'
GETN_PROJECT_CMD = 'cmake .. -G "%s" -DCMAKE_BUILD_TYPE=%s' % (compiler, CFG_BUILD_TYPE)
BUILD_PROJECT_CMD = 'cmake --build . --config %s' % (CFG_BUILD_TYPE)
PROJECT_NAME = os.path.relpath(".", "..")
GTEST_INCLUDE_DIR = os.getenv("GTEST_INCLUDE_DIR")
GTEST_LIB_DIR = os.getenv("GTEST_LIB_DIR")
FILE_TYPE_FILTER_RE = r'.*\.(h|hpp|c|cpp|cc|cxx)$'

if os.path.exists(GTEST_INCLUDE_DIR) == False:
    raise Exception("\33[91m\nGTEST_INCLUDE_DIR not exists: " + GTEST_INCLUDE_DIR + "\nsetting environment variable [GTEST_INCLUDE_DIR] \033[0m")
if os.path.exists(GTEST_LIB_DIR) == False:
    raise Exception("\33[91m\nGTEST_LIB_DIR not exists: " + GTEST_LIB_DIR + "\nsetting environment variable [GTEST_LIB_DIR] \033[0m")

def file_name_list(file_dir):
    import re
    file_list = ''
    for file in os.listdir(file_dir):
        if re.match(FILE_TYPE_FILTER_RE, file, flags=0):
            file_list += file+' '
    return file_list

CMAKE_SOURCE_STR = file_name_list(CFG_CURRENTWORK_DIR)
CMAKELISTSTXT_STR = '''
cmake_minimum_required(VERSION 3.1)
project(%s)
SET(CMAKE_DEBUG_POSTFIX "d" CACHE STRING "add a postfix, usually d on windows")
SET(CMAKE_BUILD_TYPE "Debug" CACHE STRING "build type")
if (MSVC)
  set(CMAKE_CXX_FLAGS_DEBUG "/Zi /Ob0 /Od /RTC1 /Od -DDEBUG  /MTd")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MT")
else()
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g3 -DDEBUG ")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -DNDEBUG")
endif()
IF(${CMAKE_BUILD_TYPE} MATCHES "Debug")
    SET(CMAKE_BUILD_POSTFIX "${CMAKE_DEBUG_POSTFIX}")
ELSE()
    SET(CMAKE_BUILD_POSTFIX "")
ENDIF()
SET(GTEST_INCLUDE_DIR %s)
SET(GTEST_LIB_DIR %s)
SET(THREADS_PREFER_PTHREAD_FLAG ON)
FIND_PACKAGE(Threads REQUIRED)
INCLUDE_DIRECTORIES(${GTEST_INCLUDE_DIR})
LINK_DIRECTORIES(${GTEST_LIB_DIR})
SET(SRC_TEST %s)
ADD_EXECUTABlE(${PROJECT_NAME}  ${SRC_TEST})
target_link_libraries(${PROJECT_NAME} 
gtest${CMAKE_BUILD_POSTFIX}
gtest_main${CMAKE_BUILD_POSTFIX}
Threads::Threads
)''' % (PROJECT_NAME, GTEST_INCLUDE_DIR, GTEST_LIB_DIR, CMAKE_SOURCE_STR)

def execute_cmd(cmd, self_stdout=subprocess.PIPE):
    print("\033[93msubprocess.run CMD:\033[0m", cmd)
    result = subprocess.run(cmd, stdout=self_stdout, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    if result.returncode != 0:
        str_ = str(result.stdout)
        print(str_.replace("error","\033[91merror\033[0m"))
        str_ = str(result.stderr)
        print(str_.replace("error","\033[91merror\033[0m"))       
        raise Exception("\033[91mexecute cmd failed!\033[0m")
    else:
        print("\033[92m=========execute finish!=========\033[0m")
    return result

def gen():    
    f = open("CMakeLists.txt", 'w', encoding="utf-8")
    f.write(CMAKELISTSTXT_STR)
    f.close()
    if os.path.exists(CFG_BUILD_BINARY_DIR):
        shutil.rmtree(CFG_BUILD_BINARY_DIR)
    if not os.path.exists(CFG_BUILD_BINARY_DIR):
        os.makedirs(CFG_BUILD_BINARY_DIR)
    time.sleep(2)
    os.chdir(CFG_BUILD_BINARY_DIR)
    execute_cmd(GETN_PROJECT_CMD)
    execute_cmd(BUILD_PROJECT_CMD)
    if 'Windows' in platform.platform():
        os.chdir(CFG_BUILD_TYPE)
        os.system(PROJECT_NAME)
    elif 'Linux' in platform.platform():
        os.system("./" + PROJECT_NAME)
    os.chdir(CFG_CURRENTWORK_DIR)

def execute():
    os.chdir(CFG_CURRENTWORK_DIR+"/.build")
    if 'Windows' in platform.platform():
        os.chdir(CFG_BUILD_TYPE)
        os.system(PROJECT_NAME)
    elif 'Linux' in platform.platform():
        os.system("./" + PROJECT_NAME)
    os.chdir(CFG_CURRENTWORK_DIR)

def print_global_var():
    print("\033[93mCFG_CURRENTWORK_DIR : \033[0m"+CFG_CURRENTWORK_DIR)
    print("\033[93mCFG_BUILD_TYPE : \033[0m"+CFG_BUILD_TYPE)
    print("\033[93mCFG_BUILD_BINARY_DIR : \033[0m"+CFG_BUILD_BINARY_DIR)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(usage='''
    this script generate c++ testing project by cmake tools
    do some unit testing
    generate CMakeLists.txt file in PATH where is . or setting form args.path
    CMake tools find c++ testing files in PATH''')

    parser.add_argument("-g", action="store_true", help="generate project configuration")
    parser.add_argument("-r", action="store_true", help="run testing")
    parser.add_argument("-build_type", action="store_true", default='Debug', help="build in debug")
    parser.add_argument("--path", type=str, default=".", help="testing project root dir")
    args = parser.parse_args()
    CFG_BUILD_TYPE = args.build_type
    CFG_CURRENTWORK_DIR=args.path
    CFG_BUILD_BINARY_DIR = CFG_CURRENTWORK_DIR+'/.build'
    if args.g :
        print_global_var()
        gen()
    elif args.r :
        print_global_var()
        execute()
    else:
        parser.print_help()

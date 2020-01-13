
# -*- coding: UTF-8 -*-

import platform
import os
import sys
import shutil
import time
import subprocess

if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

class GTestingConfig:
    def __init__(self):
        if 'Windows' in platform.platform():
            self.compiler = "Visual Studio 14 2015"
        elif 'Linux' in platform.platform():
            self.compiler = "Unix Makefiles"
        self.cfg_currentwork_dir = '.'
        self.cfg_build_type = 'Debug'
        self.cfg_build_binary_dir = '.build'
        self.gen_project_cmd = 'cmake .. -G "%s" -DCMAKE_BUILD_TYPE=%s' % (self.compiler, self.cfg_build_type)
        self.build_project_cmd = 'cmake --build . --config %s' % (self.cfg_build_type)
        self.project_name = os.path.relpath(".", "..")
        self.gtest_include_dir = ""
        self.gtest_lib_dir = ""
        self.include_directories = ""
        self.link_directories = ""
        self.target_link_libraries = ""
        self.source = ""
        self.file_type_filter_re = r'.*\.(h|hpp|c|cpp|cc|cxx)$'

    def generate_cmakelists(self):
        f = open(self.cfg_currentwork_dir + "/CMakeLists.txt", 'w', encoding="utf-8")
        f.write('cmake_minimum_required(VERSION 3.1)\n')
        f.write('project(%s)\n' % self.project_name)
        f.write('if (MSVC)\n')
        f.write('    SET(CMAKE_CXX_FLAGS_DEBUG "/Zi /Ob0 /Od /RTC1 /Od -DDEBUG  /MTd")\n')
        f.write('else()\n')
        f.write('    SET(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g3 -DDEBUG ")\n')
        f.write('endif()\n')
        f.write('SET(THREADS_PREFER_PTHREAD_FLAG ON)\n')
        f.write('FIND_PACKAGE(Threads REQUIRED)\n')
        f.write('INCLUDE_DIRECTORIES(%s %s)\n' % (self.gtest_include_dir, self.include_directories))
        f.write('LINK_DIRECTORIES(%s %s)\n' % (self.gtest_lib_dir, self.link_directories))
        f.write('SET(SRC_TEST %s)\n' % (self.source))
        f.write('ADD_EXECUTABlE(${PROJECT_NAME}  ${SRC_TEST})\n')
        f.write('target_link_libraries(${PROJECT_NAME} %s)' % (self.target_link_libraries))
        f.close()

    def file_name_list(self, file_dir):
        import re
        file_list = ''
        for file in os.listdir(file_dir):
            if re.match(self.file_type_filter_re, file, flags=0):
                file_list += file+' '
        return file_list

    def init(self, args):
        self.cfg_build_type = args.build_type
        self.cfg_currentwork_dir=args.path
        self.cfg_build_binary_dir = self. cfg_currentwork_dir+'/.build'
        self.project_name = os.path.relpath(self.cfg_currentwork_dir, self.cfg_currentwork_dir + "/..")
        if cfg.load_dep_configfile() == False :
            sys.exit()

        if os.path.exists(cfg.gtest_include_dir) == False:
            raise Exception("\33[91m\nGTEST_INCLUDE_DIR not exists: " +cfg. gtest_include_dir + "\033[0m")
        if os.path.exists(cfg.gtest_lib_dir) == False:
            raise Exception("\33[91m\nGTEST_LIB_DIR not exists: " + cfg.gtest_lib_dir + "\n\033[0m")

        self.generate_cmakelists()
        self.print_member_var()

    def list2str(self, list_source):
        str_source = ''
        for item in list_source:
            str_source += ( str(item) + ' ')
        return str_source

    def print_member_var(self):
        print("\033[93m compiler             : \033[0m"+self.compiler)
        print("\033[93m cfg_currentwork_dir  : \033[0m"+self.cfg_currentwork_dir)
        print("\033[93m cfg_build_type       : \033[0m"+self.cfg_build_type)
        print("\033[93m cfg_build_binary_dir : \033[0m"+self.cfg_build_binary_dir)
        print("\033[93m build_project_cmd    : \033[0m"+self.build_project_cmd)
        print("\033[93m project_name         : \033[0m"+self.project_name)
        print("\033[93m gtest_include_dir    : \033[0m"+self.gtest_include_dir)
        print("\033[93m gtest_lib_dir        : \033[0m"+self.gtest_lib_dir)
    
    def load_dep_configfile(self):
        if os.path.isfile(self.cfg_currentwork_dir+"/dep.json") == False:
            self.usage_dep_config()
            return False
        else:
            import json
            f = open(self.cfg_currentwork_dir+"/dep.json", encoding='utf-8')
            js = json.load(f)
            self.gtest_include_dir = js["gtest_include_dir"]
            self.gtest_lib_dir = js["gtest_lib_dir"]
            self.project_name = js["project_name"]
            self.include_directories = self.list2str(js["include_directories"])
            self.link_directories = self.list2str(js["link_directories"])
            self.target_link_libraries = self.list2str(js["target_link_libraries"])
            self.source = self.list2str(js["source"])
            return True

    def usage_dep_config(self):
        print("\033[92m Please configure [ " + self.cfg_currentwork_dir + "/dep.json ], example: \033[0m\n")
        print("\033[32m")
        print("{")
        print("    \"project_name\":\"googletest01\",")
        print("    \"gtest_include_dir\":\"/usr/local/googletest/include\",")
        print("    \"gtest_lib_dir\":\"/usr/local/googletest/lib\",")
        print("    \"include_directories\":[\"/usr/local/include2\", \"/usr/local/include2\"],")
        print("    \"link_directories\":[\"/usr/local/lib\",  \"/usr/local/lib64\"],")
        print("    \"target_link_libraries\":[\"pthread\", \"boost_system\"],")
        print("    \"source\":\"main.cpp\"")
        print("}")
        print("\033[0m")

cfg = GTestingConfig()

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
    if os.path.exists(cfg.cfg_build_binary_dir):
        shutil.rmtree(cfg.cfg_build_binary_dir)
    if not os.path.exists(cfg.cfg_build_binary_dir):
        os.makedirs(cfg.cfg_build_binary_dir)
    time.sleep(2)
    os.chdir(cfg.cfg_build_binary_dir)
    execute_cmd(cfg.gen_project_cmd)
    execute_cmd(cfg.build_project_cmd)
    if 'Windows' in platform.platform():
        os.chdir(cfg.cfg_build_type)
        os.system(cfg.project_name)
    elif 'Linux' in platform.platform():
        os.system("./" + cfg.project_name)
    os.chdir(cfg.cfg_currentwork_dir)

def execute():
    os.chdir(cfg.cfg_currentwork_dir+"/.build")
    if 'Windows' in platform.platform():
        os.chdir(cfg.cfg_build_type)
        os.system(cfg.project_name)
    elif 'Linux' in platform.platform():
        os.system("./" + cfg.project_name)
    os.chdir(cfg.cfg_currentwork_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(usage='''
    this script generate c++ testing project by cmake tools
    do some unit testing
    generate CMakeLists.txt file in PATH where is . or setting form args.path
    CMake tools find c++ testing files in PATH
    please GTEST_INCLUDE_DIR GTEST_LIB_DIR for environment variable''')

    parser.add_argument("-g", action="store_true", help="generate project configuration")
    parser.add_argument("-r", action="store_true", help="run testing")
    parser.add_argument("-build_type", action="store_true", default='Debug', help="build in debug")
    parser.add_argument("--path", type=str, default=".", help="testing project root dir")
    args = parser.parse_args()
    cfg.init(args)
    # sys.exit()
    if args.g :
        gen()
    elif args.r :
        execute()
    else:
        parser.print_help()

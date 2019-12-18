#!/usr/bin/sh

path_golangx="$GOPATH/src/golang.org/x"

if [ ! -d $path_golangx ];then
echo "create golang.org/x"
mkdir /data
fi

for i in "tools" "net" "sys" "text" "crypto"
do
	cd $path_golangx
    echo $i is paint
	if [ ! -d $i ];then
		git clone https://github.com/golang/$i.git
	else
		# cd $i && git pull
		echo "skip... $i"
	fi
done

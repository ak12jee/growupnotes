package main

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/Unknwon/goconfig"
	_ "github.com/go-sql-driver/mysql"
	"github.com/vmihailenco/msgpack"
)

const mainIniPath = "./conf.ini"

var (
	ConfigFile *goconfig.ConfigFile
	err        error
)

func main() {
	configPath := mainIniPath
	ConfigFile, err = goconfig.LoadConfigFile(configPath)
	if err != nil {
		panic(err)
	}

	user := ConfigFile.MustValue("global", "user", "root")
	passwd := ConfigFile.MustValue("global", "passwd", "123456")
	net := ConfigFile.MustValue("global", "net", "tcp")
	addr := ConfigFile.MustValue("global", "addr", "localhost")
	port := ConfigFile.MustInt("global", "port", 3306)
	db := ConfigFile.MustValue("global", "db", "test")
	dsn := fmt.Sprintf("%s:%s@%s(%s:%d)/%s", user, passwd, net, addr, port, db)

	DB, err := sql.Open("mysql", dsn)
	if err != nil {
		fmt.Printf("Open mysql failed,err:%v\n", err)
		return
	}
	DB.SetConnMaxLifetime(100 * time.Second)
	DB.SetMaxOpenConns(100)
	DB.SetMaxIdleConns(16)
	QueryOne(DB)
	DB.Close()
}

func QueryOne(db *sql.DB) {
	if db == nil {
		return
	}
	sql := ConfigFile.MustValue("global", "sql", "")
	rows, err := db.Query(sql)
	if err != nil {
		rows.Close()
		fmt.Println(err)
		return
	}

	for rows.Next() {
		columns, _ := rows.Columns()

		scanArgs := make([]interface{}, len(columns))
		values := make([]interface{}, len(columns))

		for i := range values {
			scanArgs[i] = &values[i]
		}

		err = rows.Scan(scanArgs...)
		record := make(map[string][]byte)
		for i, col := range values {
			if col != nil {
				record[columns[i]] = col.([]byte)
			}
		}
		tag := ConfigFile.MustValue("global", "tag", "tgs")
		if v, ok := record[tag]; ok {
			var ret interface{}
			err := msgpack.Unmarshal(v, &ret)
			if err != nil {
				fmt.Println(err)
			} else {
				fmt.Println(ret)
			}
		}
	}
	rows.Close()
}

package main

import (
	"fmt"
	"github.com/BurntSushi/toml"
	"github.com/gin-gonic/gin"
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
	"io"
	"os"
	"path/filepath"
	"time"
)

type UserInfo struct {
	Name  string `json:"name"`
	Desc  string `json:"description"`
	Image string `json:"image"`
	Realm string `json:"realm"`
}
type Rss360 struct {
	Title          string   `json:"title"`
	Content        string   `json:"content"`
	PublishTime    string   `json:"publish_time"`
	Url            string   `json:"url"`
	ArticleType    string   `json:"article_type"`
	VideoSourceUrl string   `json:"video_source_url"`
	CoverPicture   string   `json:"cover_picture"`
	VideoSuffix    string   `json:"video_suffix"`
	UserInfo       UserInfo `json:"user_info"`
}

type tomlConfig struct {
	MongodbAddr       string
	DefaultDB         string
	DefaultCollection string
	ServerIP          string
}

var cfg tomlConfig
var session *mgo.Session
var db *mgo.Database
var cc *mgo.Collection
var pwd string

func init() {
	path, _ := os.Executable()
	pwd = filepath.Dir(path)
	fmt.Println("pwd : ", pwd)
	cfgPath := fmt.Sprintf("%s/config.toml", pwd)
	fmt.Println("cfg path : ",cfgPath)
	if _, err := toml.DecodeFile(cfgPath, &cfg); err != nil {
		fmt.Println(err)
	} else {
		fmt.Println("cfg : ",cfg)
	}
	dialInfo := &mgo.DialInfo{
		Addrs:     []string{cfg.MongodbAddr},
		Direct:    false,
		Timeout:   time.Second * 1,
		Database:  cfg.DefaultDB,
		PoolLimit: 4096, // Session.SetPoolLimit
	}
	session, err := mgo.DialWithInfo(dialInfo)
	if err != nil {
		panic(err)
	}
	session.SetMode(mgo.Monotonic, true)
	db = session.DB(cfg.DefaultDB)
	cc = db.C(cfg.DefaultCollection)
}
func handlerRss(c *gin.Context) {
	var result []Rss360
	cc.Find(bson.M{}).All(&result)
	c.JSON(200, result)
}
func stop() {
	defer session.Close()
}
func main() {
	f, _ := os.Create(fmt.Sprintf("%s/gin.log", pwd))
	gin.DefaultWriter = io.MultiWriter(f)
	r := gin.Default()
	r.GET("/v1/rss", handlerRss)
	r.Run(cfg.ServerIP)
	stop()
}

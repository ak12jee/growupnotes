package main

import (
	l4g "github.com/alecthomas/log4go"
	"github.com/robfig/cron"
)

func text() {
	l4g.Info("text")
}

func main() {
	c := cron.New()
	c.AddFunc("* * * * * *", func() { text() })
	c.Start()
	select {}
}

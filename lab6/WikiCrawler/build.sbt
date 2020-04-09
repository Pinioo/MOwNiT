name := "WikiCrawler"

version := "0.1"

libraryDependencies ++= Seq(
  "com.typesafe.play" %% "play-json" % "2.8.1",
  "com.typesafe.play" %% "play" % "2.8.1",
  "com.typesafe.play" %% "play-ahc-ws-standalone" % "2.1.2",
  "com.typesafe.play" %% "play-ws-standalone-json" % "2.1.2",
  "com.typesafe.play" %% "play-ws-standalone-xml" % "2.1.2"
)

scalaVersion := "2.13.1"

package org.pinioo.wikicrawler.crawler

import java.io.{File, FileWriter}
import java.util.concurrent.CompletionStage

import play.libs.ws.ahc.StandaloneAhcWSClient
import play.libs.ws.JsonBodyReadables.instance.json
import akka.actor.ActorSystem
import akka.stream.Materializer
import com.fasterxml.jackson.databind.JsonNode
import play.shaded.ahc.org.asynchttpclient.DefaultAsyncHttpClient
import play.shaded.ahc.org.asynchttpclient.DefaultAsyncHttpClientConfig

import scala.jdk.CollectionConverters._

case object Crawler extends App {
  def getRandomTitles(n: Int)(implicit ws: StandaloneAhcWSClient): Seq[String] = {
    val iters = n / 500 + 1
    val toGetInIter = n / iters
    for {
      _ <- 1 to iters
      i <- ws.url(s"https://en.wikipedia.org/w/api.php?format=json&action=query&generator=random&grnnamespace=0&grnlimit=${toGetInIter}").get.thenApply[JsonNode] {
        _
          .getBody(json())
          .at("/query/pages")
      }.toCompletableFuture.get.elements.asScala.map(_.at("/title").asText.replace(' ', '_'))
    } yield i
  }

  def saveWikiArticle(title: String, text: String)(dir: Option[String]): Unit = {
    var directoryPath: String = ""

    dir match {
      case Some(path) =>
        directoryPath = path
        val dirFile = new File(path)
        if (!dirFile.isDirectory)
          dirFile.mkdir()
      case None =>
        directoryPath = "."
    }

    val f = new File(s"${directoryPath}/${title}.txt")
    if(!f.exists()) {
      f.createNewFile()
      val fw = new FileWriter(f)
      fw.write(text)
      fw.close()
    }
  }

  def crawl(title: String)(implicit ws: StandaloneAhcWSClient): CompletionStage[String] = {
    val url = s"https://en.wikipedia.org/w/api.php?action=parse&page=${title}&prop=wikitext&formatversion=2&format=json"

    ws.url(url).get().thenApply[String] {
      _
        .getBody(json())
        .at("/parse/wikitext")
        .asText()
    }
  }

  def getRandomArticles(n: Int)(dir: Option[String] = None): Unit = {
    val name = "wsclient"
    val system = ActorSystem.create(name)
    val materializer = Materializer.matFromSystem(system)

    val asyncHttpClientConfig = new DefaultAsyncHttpClientConfig.Builder().setMaxRequestRetry(0).setShutdownQuietPeriod(0).setShutdownTimeout(0).build
    val asyncHttpClient = new DefaultAsyncHttpClient(asyncHttpClientConfig)

    implicit val client = new StandaloneAhcWSClient(asyncHttpClient, materializer)

    var counter = 0;

    for(title <- getRandomTitles(n)){
      crawl(title).thenAccept(saveWikiArticle(title, _)(dir)).thenAccept(_ => counter += 1)
    }

    while(counter < n){
      Thread.sleep(1000)
    }

    system.terminate()
    client.close()
  }

  if(args.length < 1)
    throw new Exception

  val articlesToFind = args(0).toInt
  val pathToSave =
    if(args.length < 2)
      None
    else
      Some(args(1))

  getRandomArticles(articlesToFind)(pathToSave)
}

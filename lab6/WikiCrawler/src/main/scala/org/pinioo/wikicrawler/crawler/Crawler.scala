package org.pinioo.wikicrawler.crawler

import java.io.{File, FileWriter}
import java.util.concurrent.TimeUnit

import play.libs.ws.ahc.StandaloneAhcWSClient
import play.libs.ws.JsonBodyReadables.instance.json
import akka.actor.ActorSystem
import akka.stream.Materializer
import com.fasterxml.jackson.databind.JsonNode
import play.shaded.ahc.org.asynchttpclient.DefaultAsyncHttpClient
import play.shaded.ahc.org.asynchttpclient.DefaultAsyncHttpClientConfig

import scala.collection.mutable
import scala.concurrent.{Await, Future}
import scala.jdk.CollectionConverters._
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.duration.Duration
import scala.util.{Failure, Success, Try}



case object Crawler extends App {
  val jsonMap = mutable.HashMap[String, JsonNode]()

  def getRandomPageIDs(n: Int)(implicit ws: StandaloneAhcWSClient): Seq[String] = {
    var toGetInIter = List[Int]()
    var left = n

    while(left > 0){
      if(left > 500)
        toGetInIter = 500 +: toGetInIter
      else
        toGetInIter = left +: toGetInIter
      left -= toGetInIter.head
    }

    for {
      generatorLimit <- toGetInIter
      i <- ws.url(s"https://en.wikipedia.org/w/api.php?format=json&action=query&generator=random&grnnamespace=0&grnlimit=${generatorLimit}").get.thenApply[JsonNode] {
        _
          .getBody(json())
          .at("/query/pages")
      }.toCompletableFuture.get.elements.asScala.map(_.at("/pageid").asText)
    } yield i
  }

  def getPageBody(pageid: String)(implicit ws: StandaloneAhcWSClient): JsonNode = {
    if(!jsonMap.contains(pageid)) {
      val url = s"https://en.wikipedia.org/w/api.php?action=parse&pageid=${pageid}&prop=wikitext&formatversion=2&format=json"
      jsonMap.addOne(pageid -> ws.url(url).get().thenApply[JsonNode] {
        _
          .getBody(json())
      }.toCompletableFuture.get)
    }
    jsonMap(pageid)
  }

  def saveWikiArticle(pageid: String, text: String)(dir: Option[String])(implicit ws: StandaloneAhcWSClient): Unit = {
    getPageBody(pageid).getWikititleOpt match {
      case Some(title) =>
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

        val f = new File(s"${directoryPath}/${title.replace('/', '_')}.txt")
        if(!f.exists()) {
          Try{
            f.createNewFile()
            val fw = new FileWriter(f)
            fw.write(text)
            fw.close()
          } match {
            case Success(_) =>
              ()
            case Failure(e) =>
              println(f.getAbsolutePath + " caused problems:")
              println(e.getMessage)
              println("-----------------------------")
          }
        }
      case None => ()
    }
  }

  def crawl(pageid: String)(implicit ws: StandaloneAhcWSClient): String = {
    val result = getPageBody(pageid)
      .getWikitextOpt
      .map {
        _
          .replaceAll("[^A-Za-z0-9]", " ")
          .replaceAll(" +", " ")
      }
      .getOrElse("")

    if(result.length > 5000) result.substring(0, 5000)
    else result
  }

  def getRandomArticles(n: Int)(dir: Option[String] = None): Unit = {
    val name = "wsclient"
    val system = ActorSystem.create(name)
    val materializer = Materializer.matFromSystem(system)

    val asyncHttpClientConfig = new DefaultAsyncHttpClientConfig.Builder().setMaxRequestRetry(0).setShutdownQuietPeriod(0).setShutdownTimeout(0).build
    val asyncHttpClient = new DefaultAsyncHttpClient(asyncHttpClientConfig)

    implicit val client: StandaloneAhcWSClient = new StandaloneAhcWSClient(asyncHttpClient, materializer)

    Await.result(Future.sequence(getRandomPageIDs(n).map{
      pageid => Future{
        val wikitext = crawl(pageid)
        saveWikiArticle(pageid, wikitext)(dir)
      }
    }), Duration(500*n, TimeUnit.MILLISECONDS))

    system.terminate()
    client.close()
  }

  if(args.length < 1)
    throw new IndexOutOfBoundsException("Articles quantity must be provided")

  val articlesToFind = args(0).toInt
  val pathToSave =
    if(args.length < 2)
      None
    else
      Some(args(1))

  implicit class WikiNode(jsonNode: JsonNode){
    def getWikitextOpt: Option[String] = {
      if(jsonNode.has("parse") && jsonNode.at("/parse").has("wikitext"))
        Some(jsonNode.at("/parse/wikitext").asText())
      else
        None
    }

    def getWikititleOpt: Option[String] = {
      if(jsonNode.has("parse") && jsonNode.at("/parse").has("title"))
        Some(jsonNode.at("/parse/title").asText().replace(' ', '_'))
      else
        None
    }
  }

  getRandomArticles(articlesToFind)(pathToSave)
}


package org.pinioo.wikicrawler.crawler

import java.io.{File, FileWriter}
import java.util.concurrent.{Executors, ThreadPoolExecutor, TimeUnit}

import play.libs.ws.ahc.StandaloneAhcWSClient
import play.libs.ws.JsonBodyReadables.instance.json
import akka.actor.ActorSystem
import akka.stream.Materializer
import com.fasterxml.jackson.databind.JsonNode
import play.shaded.ahc.org.asynchttpclient.DefaultAsyncHttpClient
import play.shaded.ahc.org.asynchttpclient.DefaultAsyncHttpClientConfig

import scala.collection.mutable
import scala.concurrent.{Await, ExecutionContext, ExecutionContextExecutorService, Future}
import scala.jdk.CollectionConverters._
import scala.concurrent.duration.Duration
import scala.util.{Failure, Success, Try}



case object Crawler extends App {
  val jsonMap = mutable.HashMap[String, JsonNode]()

  val executorService = Executors.newFixedThreadPool(1000);

  implicit val executionContext: ExecutionContextExecutorService = ExecutionContext.fromExecutorService( executorService )


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

  def getPageBody(pageid: String)(implicit ws: StandaloneAhcWSClient): Option[JsonNode] = {
    if(!jsonMap.contains(pageid)) {
      val url = s"https://en.wikipedia.org/w/api.php?action=parse&pageid=${pageid}&prop=wikitext&formatversion=2&format=json"
      Try {
        jsonMap.addOne(pageid -> ws.url(url).get().thenApply[JsonNode] {
          _
            .getBody(json())
        }.toCompletableFuture.get)
      } match {
        case Success(_) =>
          ()
        case Failure(_) =>
          println(s"Wikimedia error for ID: ${pageid}")
      }
    }
    if(jsonMap.contains(pageid))
      Some(jsonMap(pageid))
    else
      None
  }

  def saveWikiArticle(pageid: String, text: String)(dir: Option[String])(implicit ws: StandaloneAhcWSClient): Int = {
    getPageBody(pageid).map(_.getWikititleOpt match {
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
          Try {
            f.createNewFile()
            val fw = new FileWriter(f)
            fw.write(text)
            fw.close()
          } match {
            case Success(_) =>
              1
            case Failure(e) =>
              println(f.getAbsolutePath + " caused problems:")
              println(e.getMessage)
              println("-----------------------------")
              0
          }
        } else 0
      case None =>
        println(s"Failed to get content of page with ID: ${pageid}")
        0
    }).getOrElse(0)
  }

  def crawl(pageid: String)(implicit ws: StandaloneAhcWSClient): Option[String] = {
    getPageBody(pageid)
      .map {
      _.getWikitextOpt
        .map {
          _
            .replaceAll("[^A-Za-z0-9]", " ")
            .replaceAll(" +", " ")
        }
        .getOrElse("")
      }.map {
      result => {
        if (result.length > 5000)
          result.substring(0, 5000)
        else
          result
        }
      }
  }

  def getRandomArticles(n: Int)(dir: Option[String] = None): Unit = {
    val name = "wsclient"
    val system = ActorSystem.create(name)
    val materializer = Materializer.matFromSystem(system)

    val asyncHttpClientConfig = new DefaultAsyncHttpClientConfig.Builder().setMaxRequestRetry(0).setShutdownQuietPeriod(0).setShutdownTimeout(0).build
    val asyncHttpClient = new DefaultAsyncHttpClient(asyncHttpClientConfig)

    implicit val client: StandaloneAhcWSClient = new StandaloneAhcWSClient(asyncHttpClient, materializer)

    var left = n
    while(left > 0) {
      println(s"${left} left")
      val toGen = if(left > 1000) 1000 else left
      Await.ready(Future.sequence(getRandomPageIDs(toGen).map {
        pageid =>
          Future {
            crawl(pageid).map {
              saveWikiArticle(pageid, _)(dir)
            }.getOrElse(0)
          }
      }), Duration(50 * toGen, TimeUnit.MILLISECONDS)).value.get match {
        case Failure(e) =>
          e.printStackTrace()
        case Success(s) =>
          println(s"Generated ${s.sum}")
          left -= s.sum
      }
      if (left > 0) {
        println("Waiting 5s")
        Thread.sleep(5000)
      }
      else
        println("Done")
    }
    executionContext.shutdown()

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
      Try {
        jsonNode.at("/parse/wikitext").asText()
      } match {
        case Success(s) => Some(s)
        case Failure(_) => None
      }
    }

    def getWikititleOpt: Option[String] = {
      Try {
        jsonNode.at("/parse/title").asText().replace(' ', '_')
      } match {
        case Success(s) => Some(s)
        case Failure(_) => None
      }
    }
  }

  getRandomArticles(articlesToFind)(pathToSave)
}


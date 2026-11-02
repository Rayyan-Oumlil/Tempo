
# tactiq.io free youtube transcript

# Scanners with Interactive Brokers API in Python with ib-insync / ib-async

# https://www.youtube.com/watch/E2JE8fPaC5s

00:00:00.640 hello everyone finally I'm back with
00:00:02.600 another IB insync IB async video for
00:00:06.399 those who are new IB async is the new
00:00:08.519 version of IB insync that will be
00:00:10.960 maintained um in this video we're going
00:00:13.280 to be talking about scanners so I'll
00:00:15.759 show you how to do that with IB insync
00:00:18.359 IB async um first of all for those who
00:00:20.960 are not familiar um scanners are often
00:00:23.320 used by people like day Traders they
00:00:25.480 like to identify stocks that meet
00:00:27.519 certain criteria so to give you an
00:00:29.640 example like they look for maybe opening
00:00:31.439 gappers like stocks that are like up
00:00:33.719 premarket like a lot a lot compared to
00:00:36.239 the previous day close they might look
00:00:38.239 at low float stocks they might also just
00:00:40.399 like filter the universe of stocks to
00:00:42.239 anything like they want stocks with
00:00:44.200 above a market cap of $100 million uh
00:00:47.079 below a uh uh below a market cap of a
00:00:50.840 billion between $10 and $100 so these uh
00:00:54.520 scanners allow you to search the whole
00:00:56.039 vast Universe of instruments and get
00:00:59.039 what you're looking for and that helps a
00:01:01.079 lot of Traders out so let's get started
00:01:03.640 um first I'll show you guys like um the
00:01:05.680 trader workstation like how it looks
00:01:08.200 like because these scanners uh in the
00:01:10.799 API correspond one to one to the trader
00:01:13.439 workstation versions so first let's look
00:01:15.680 at the trader workstation so oops sorry
00:01:19.119 I um so you do like file um a new window
00:01:23.799 uh and then there's a thing called
00:01:25.000 scanners and oh to be exact it
00:01:27.799 corresponds to the advanced Market
00:01:29.280 scanner okay so you can do a scan so
00:01:32.040 like by default it's showing you like
00:01:34.000 wow the top percentage gainers this
00:01:36.600 stock uh I don't know if any of you
00:01:38.320 heard of it rcml is up 7,400 per. but no
00:01:42.920 none of us have heard of it so uh it
00:01:44.799 probably is a penny stock yeah see it's
00:01:46.360 a penny stock so why don't we um we we
00:01:49.000 limit our stocks to stocks above $150
00:01:51.759 right so then when we search we get all
00:01:54.799 the stocks above
00:01:56.200 $150 that's like a a filter and now it's
00:02:00.079 that maybe some of us know a little bit
00:02:03.000 better but so basically yeah you have
00:02:05.399 all these filters you can use you can
00:02:06.759 have greater than $150 you can look at
00:02:09.639 um top percent gainers top percent
00:02:11.760 losers most active uh halted there's
00:02:15.319 like a million things you can search by
00:02:17.879 um so we can look at the top percent
00:02:19.920 losers uh we'll see our um our good
00:02:22.920 friends at Tesla there unfortunately
00:02:24.760 like always um
00:02:30.040 okay uh so top percent losers you see
00:02:32.800 our good friends at Tesla down uh almost
00:02:36.440 5% uh because some uh um Cu uh um
00:02:41.640 Executives leaving that sort of thing
00:02:43.920 coinbase uh is also down quite a bit um
00:02:47.920 okay so now we can edit it um also we
00:02:50.319 can do things like um uh we can do
00:02:53.280 things like uh top trade count uh this
00:02:56.280 is an interesting one for a lot of
00:02:57.840 people it's like top percent uh uh top
00:03:01.319 close to open percent gainers this is
00:03:04.000 like the people with the highest opening
00:03:05.879 Gap so uh this thing wire was gapped up
00:03:09.920 10.72% that means the opening price
00:03:12.519 today is 10% higher than the closing
00:03:14.799 price yesterday so basically I'm going
00:03:17.239 to show you guys how to do all this
00:03:18.959 stuff with the API and I'm also going to
00:03:22.040 show all these things all these things
00:03:24.000 have like a exact mapping to the API so
00:03:27.440 um let's get started with the API um
00:03:30.480 okay
00:03:31.380 [Music]
00:03:32.519 um okay let me just close this I'm not
00:03:35.680 using Trader workstation for um uh I use
00:03:39.480 always IB Gateway but since I have two
00:03:41.159 users I'm just going to keep it open
00:03:42.599 just in case we need it later so uh
00:03:45.319 first thing we're going to do is let's
00:03:46.680 connect to IB as in all my other videos
00:03:50.040 so if you use ibas sync this would be
00:03:52.000 from ibas sync import Star oops I guess
00:03:54.480 I used this
00:03:55.560 already uh
00:04:00.239 so let me
00:04:02.239 connect okay so let me show you guys the
00:04:04.640 first simple example is you have to do
00:04:06.480 like a subscription is scanner
00:04:09.280 subscription and then what do you do you
00:04:11.640 give it like a number of rows to return
00:04:13.879 50 I think is the max if you put 100
00:04:15.799 it'll still give you 50 you give it an
00:04:17.519 instrument it could be like a stock bond
00:04:19.880 that sort of thing later I'll show you
00:04:21.600 the possible instruments um you give it
00:04:24.120 a location code uh there's something
00:04:26.440 called stock. us. major those are the
00:04:29.759 major US stock exchanges um like NASDAQ
00:04:33.840 New York Stock Exchange that sort of
00:04:35.160 thing um and then what's important is
00:04:37.680 you have to have this like scan code
00:04:39.199 this is what you're searching by so top
00:04:41.680 percent gain and later I'll show you
00:04:44.360 like there's like this XML file you can
00:04:46.479 get um which will like correspond to
00:04:49.600 like what things were called um in the
00:04:52.240 um Trader workstation so remember in
00:04:55.160 Trader workstation it wasn't called
00:04:57.240 topor perc gain it was actually called
00:05:00.039 um top percentage gainers right so if
00:05:04.039 search here it'll be top percentage
00:05:06.199 gainers and then you'll see like this is
00:05:08.639 the display name and the uh scan code is
00:05:11.680 top percent gain so I'll show you how to
00:05:13.919 get that XML in a in a bit but just the
00:05:16.520 most basic subscription is like let's
00:05:18.280 say we're doing the um the top percent
00:05:20.800 gain so now I can do um uh I can get
00:05:25.160 scan data like I can do like um SC uh
00:05:29.000 scan
00:05:30.280 data equals ib. Rec scan uh uh scanner
00:05:35.000 data sub and then I can get the scan
00:05:39.759 data
00:05:41.919 um uh oh I I didn't spell top percent
00:05:44.720 gain right it's like this so now I get
00:05:47.039 scan data okay so this is just like a
00:05:50.000 scan data and then you can add all these
00:05:52.840 filters like there's there's a lot of
00:05:54.680 filters that um come as arguments so I
00:05:57.440 can add like uh let's say I can do
00:05:59.240 Market cap market cap is in uh millions
00:06:02.319 of dollars market cap let's do above um
00:06:06.000 one uh let's do a and this is like a um
00:06:11.000 a comma basically so if 1 million time a
00:06:13.840 million is how much I think that's a
00:06:15.680 trillion and then let's do above price
00:06:18.720 above uh do like above above
00:06:22.759 uh oh there's always an ordering thing
00:06:25.240 so maybe that's weird actually um above
00:06:29.759 price equals let's say 100 and
00:06:34.400 above uh volume equals let's say this
00:06:38.639 thing and let's see what we get uh we
00:06:41.560 didn't get anything um so uh percent uh
00:06:46.280 loss let's try uh oops
00:06:53.400 uh%
00:06:55.039 gain uh why are we getting nothing um
00:06:58.919 could it be that all the things in our
00:07:00.639 criteria by the way uh when you're using
00:07:03.039 top percent gain um if there is no
00:07:06.639 stocks uh that fit the criteria you get
00:07:09.120 nothing those stocks that are uh
00:07:11.360 positive percent gain you get nothing so
00:07:13.319 it could be that's the case uh let's
00:07:15.639 look at what the percent loss is
00:07:17.080 actually uh so let's do top percent um
00:07:20.960 losers it's called top Pur loss um it
00:07:25.280 could be that now the market is down and
00:07:27.560 like all the ones with if I use like a
00:07:30.000 million and then I do a million because
00:07:31.599 a million is a trillion all the trillion
00:07:33.879 dollar market caps are all down that
00:07:35.720 could be a reason so let's try let's see
00:07:38.000 if that's the reason so let's do a top
00:07:40.120 percent loss that's the reason exactly
00:07:42.720 so now we we see we have the rank of
00:07:44.639 these things um but um it doesn't give
00:07:48.720 us that much information so we can do
00:07:50.400 like of course um we can uh look at
00:07:54.520 .df scan
00:07:57.680 data so uh just explain for a second
00:08:00.840 this is because a million time a million
00:08:02.759 is a trillion and all the stocks above a
00:08:06.240 trillion dollars and above hundred a
00:08:08.919 trillion dollar market cap and above a
00:08:10.919 $100 stock price and this volume
00:08:13.720 criteria all of them were are down now
00:08:16.759 so that's why it return nothing okay um
00:08:20.319 but like if you order by top percent
00:08:22.280 loss you do get um a few there's not
00:08:24.759 that many stocks of course with over a
00:08:26.280 trillion market cap you know uh but
00:08:28.840 anyways um uh yeah so we can look at the
00:08:31.759 data and you see it gives us like this
00:08:33.919 um uh contract details object and um the
00:08:38.479 contracts detail object you can have
00:08:40.479 like some sort of scratch paper like I
00:08:42.799 can have like a scratch. py and I can
00:08:45.080 look at uh uh contract details and I do
00:08:48.600 control B and I see like okay there's a
00:08:50.880 contract in that so we can actually get
00:08:52.760 the contract so let's show you guys how
00:08:55.279 to do that let's clean this thing up so
00:08:57.600 we can define define a function called
00:09:00.160 um display with stock symbol um this is
00:09:04.200 uh so what what we can do in this thing
00:09:06.880 is um is we can basically um we can do
00:09:11.519 uh .df to get the data frame uh we can
00:09:14.880 get the contract by by doing the apply
00:09:17.480 method contract details and taking out
00:09:19.519 the contract and then we can show the
00:09:21.399 symbol by using that symbol method of
00:09:23.279 the contract and we can return the data
00:09:24.800 frame so um let me show you how that
00:09:27.440 looks that's display uh with stock
00:09:29.519 symbol scan data and that looks like
00:09:32.680 this so uh meta is the uh worst stock
00:09:37.040 today um Nvidia Microsoft Apple and then
00:09:40.640 Amazon in it ranking by worst uh let's
00:09:44.160 actually uh lower the market cap a bit
00:09:46.240 so we can get Tesla in there let's do
00:09:47.839 like 300,000 three that that makes it
00:09:50.680 300 million and above so let's get our
00:09:52.959 friends Tesla some
00:09:54.680 love um so you see now Tesla is the
00:09:57.160 worst right but you see like met is the
00:09:59.640 second worst uh broad cam is the third
00:10:01.720 worst and so on so this is kind of
00:10:03.560 annoying because like we don't have the
00:10:05.480 actual Market data so um so as I said
00:10:09.040 here it's annoying without the market
00:10:10.480 data so we are going to have to like
00:10:12.800 separately request the market data so
00:10:15.040 let me just remind you guys maybe like
00:10:16.680 how you could do this you can like uh do
00:10:19.360 the ib. market data function so let's do
00:10:22.200 like ticker dict equals this and then
00:10:25.079 let's do for contract
00:10:27.760 in uh
00:10:29.920 display in in whatever this thing is
00:10:32.600 I'll do do contract. two list I can do I
00:10:37.519 um ticker dict um
00:10:41.320 contract um equals ib.
00:10:46.760 Rec uh Market
00:10:49.639 data
00:10:51.959 contract um so let me remind you guys
00:10:54.360 what these things are contract is the
00:10:56.399 contract um this is like uh uh generic
00:10:59.800 tick list I'm going to use the default
00:11:02.360 um the next two are important uh um
00:11:05.079 snapshot let's do snapshot equals true
00:11:07.839 snapshot equals false means um it'll
00:11:10.720 constantly update the object and it'll
00:11:13.320 give you like a real Market data keep
00:11:15.800 that keeps going on but we want we'll
00:11:17.800 just do we just want one snapshot
00:11:19.480 because I don't want it to keep going I
00:11:20.920 want it to like update with um like if
00:11:23.560 the scanner updates and I don't want um
00:11:25.800 so this will do one shot and it'll not
00:11:28.000 update that's snapshot equals true and
00:11:30.600 then this is there's this like
00:11:31.959 regulatory snapshot let's do equals
00:11:34.279 false that gives you like the best
00:11:37.360 national best bid offer uh thing uh we
00:11:40.279 don't want to pay for that okay so now
00:11:42.200 how does the ticker dick look like we
00:11:44.200 can also add like this um let's add a
00:11:48.279 you can always add like ib. sleep
00:11:51.399 because sometimes it doesn't fill right
00:11:52.800 away if you want to call it so now if
00:11:54.959 you look at ticker dick we have a
00:11:56.839 dictionary with the keys being the
00:11:58.760 contract
00:11:59.760 and the values being the uh the uh um
00:12:04.519 ticker so we can also like look at this
00:12:07.200 as a data
00:12:10.000 frame and we okay we have the contract
00:12:12.639 the time Market data type um bid ask
00:12:16.560 Greeks all that good stuff so um so yeah
00:12:20.320 we can use
00:12:21.720 this uh to create um so basically we can
00:12:25.560 use this thing to um uh to to make the
00:12:29.839 uh the um scanner have this uh
00:12:33.839 information the market data so I can um
00:12:38.480 okay so like and by the way the
00:12:40.079 important things here is uh the
00:12:42.279 important things are there's a thing
00:12:43.880 called close close is the closing price
00:12:47.079 yesterday last is the last trade price
00:12:50.120 and then there's bid ask those are
00:12:51.519 probably the the things the most
00:12:53.680 relevant to us right now so um okay so
00:12:57.760 let me just copy this this let me we can
00:13:00.199 dis we can have a function called
00:13:03.040 display with stock symbol and Market
00:13:06.399 data and I'm going to have two inputs
00:13:08.560 the scan data and the tickers dick and
00:13:10.600 then show you guys how it would work so
00:13:13.839 um as I showed you guys previously um I
00:13:17.320 could
00:13:18.920 um uh uh okay sorry I could use I could
00:13:21.680 actually use this function display with
00:13:23.920 stock symbol I can call this
00:13:26.040 thing
00:13:28.120 um I can do like uh DF equals display
00:13:32.000 with stock symbol and then Market data
00:13:35.160 data frame I can do the what we did
00:13:37.240 above tickers dick. values um and um
00:13:42.360 let's add a thing called a symbol to
00:13:44.760 that so the symbol uh remember the that
00:13:48.720 values the it had a contract so we can
00:13:51.560 do contract that symbol and then we get
00:13:53.600 the um Market data uh data frame with
00:13:56.680 the symbol object okay and then we can
00:13:59.800 join it with the um data frame from the
00:14:03.759 um scanner and that gives us like um a
00:14:07.320 merge data frame with the market data so
00:14:10.680 um so now let's let's run this for a
00:14:13.240 second and then we we can get
00:14:15.480 um display uh with stock
00:14:19.240 symbol uh oh let me run this
00:14:24.560 um and Market data scan data tickers
00:14:28.720 dict
00:14:30.680 and this is what we wanted we wanted
00:14:32.440 like okay Tesla has the bid ask last and
00:14:36.279 then close so um Tesla's the down the
00:14:40.279 most it's down uh like this um so maybe
00:14:44.839 we can actually add the um percent
00:14:47.399 change here DF merged uh
00:14:52.079 percent change equals DF uh uh merged
00:14:58.560 closed
00:14:59.560 minus DF
00:15:01.759 merged
00:15:03.519 um sorry last like today's the last
00:15:07.800 trade price minus last uh session's
00:15:11.399 close
00:15:13.519 over um last session's
00:15:16.639 closed and then we get the percent
00:15:19.160 change uh I'll call it
00:15:22.480 um I don't want to get into too much
00:15:24.680 detail on formatting the data frame but
00:15:26.720 like uh maybe like that that we get the
00:15:30.120 percent change so Tesla is the worst
00:15:31.920 down almost
00:15:33.800 5% um and then meta uh broadcom and so
00:15:37.560 on so this is just like a a way to look
00:15:40.040 at it um nicer so um let me just show
00:15:44.160 you guys like um let's just make it end
00:15:46.600 to end where like instead of like
00:15:48.639 requesting the um we do the like uh
00:15:52.279 wreck scan scanner data let's just do
00:15:55.160 the whole process like end to end uh
00:15:58.079 instead of in part
00:15:59.560 so we can uh actually um create this
00:16:02.360 function we'll do um get uh Scanner with
00:16:05.399 Market data and then I'll do uh uh just
00:16:09.079 the steps above scan data equals ib. Rec
00:16:13.800 uh scanner data sub um and then I'll do
00:16:17.759 DF equals display
00:16:20.519 um uh with stock symbol uh scan
00:16:26.079 data and then um uh we'll create the
00:16:29.680 ticker dick as above so the ticker dick
00:16:32.199 was like
00:16:33.440 here um oops
00:16:37.079 sorry
00:16:44.079 uh so let's do uh DF doc contract. to
00:16:48.519 list so we go over all the contracts
00:16:51.160 from the scanner results and we um
00:16:54.759 basically uh uh get the market data
00:16:57.680 snapshot
00:16:59.319 um okay and then uh we're going to at
00:17:02.519 the end call this method to get uh the
00:17:05.359 format we want so we'll do um
00:17:09.240 return um this this dude and then um so
00:17:13.400 let's let's run it let's uh let's do um
00:17:17.319 get Scanner with Market data and then
00:17:20.720 sub is the um scanner subscription let's
00:17:23.599 see how it looks like um let me see one
00:17:26.319 second
00:17:27.599 okay so we
00:17:33.799 get ah ticker's dick uh uh ticker dick
00:17:39.280 not ticker
00:17:41.160 dick ignore these messages um so you see
00:17:46.080 Tesla uh meta and we get the percent
00:17:48.600 change and everything and the rank is
00:17:50.919 like in the scanner where it appears
00:17:53.000 okay so that's this um we can also uh
00:17:56.240 remember I showed you like the uh
00:17:57.880 opening Gap uh thing so we can also try
00:18:00.679 a different subscription we can uh uh
00:18:03.080 let's look at like the opening Gap we
00:18:04.760 can do um sub equals scanner
00:18:07.880 subscription um let's do uh number of
00:18:11.559 rows equals 50 uh instrument equals
00:18:16.120 stock uh loc same as last time location
00:18:19.240 code stock.
00:18:20.960 us. uh
00:18:24.760 major uh
00:18:32.159 um above price let's do 100 and then
00:18:34.960 let's uh do now scan code
00:18:39.000 oops uh scan code equals
00:18:44.320 High open Gap and I probably made a typo
00:18:49.159 but let's
00:18:50.360 check um so this now we'll search it by
00:18:53.039 uh High opening
00:18:55.919 gaps oops oh ignore these errors so oh
00:19:00.240 remember the wire example we saw in when
00:19:02.840 we checked ourselves we saw wire was the
00:19:04.840 top opening Gap the Gap was
00:19:07.880 10.72% let's actually see if we can get
00:19:10.240 the numbers to match up um so to get the
00:19:13.039 opening Gap uh you need the opening
00:19:15.360 price um so the opening price um I'm
00:19:19.679 pretty sure it's called ticker do open
00:19:22.240 let's let me uh let me see if this works
00:19:25.280 just one second um I'll add open here um
00:19:29.200 and then I'll add a open
00:19:32.559 here and then uh we'll have a percent
00:19:35.679 change and then let's have the
00:19:38.840 um uh Gap percent we'll do a gap percent
00:19:43.440 percent uh uh maybe I'll call it Gap
00:19:46.360 percent and then the Gap percent would
00:19:48.600 be like the opening price today minus
00:19:51.400 the close of yesterday over the close of
00:19:53.679 yesterday so I'll call it Gap percent I
00:19:56.520 don't know if this works I I didn't try
00:19:58.360 it this is just like me doing it now so
00:20:02.080 I guess it does work um and uh when we
00:20:05.159 search by the top
00:20:09.720 gappers um we see the Gap percent is
00:20:13.480 10.7 211 uh it's it doesn't quite get to
00:20:18.200 the same one as oh it does okay we're
00:20:20.919 good okay great um sorry uh I'm using my
00:20:24.880 Hotspot I have 7% battery so we have 7%
00:20:28.679 to finish this rest of this video okay
00:20:31.200 so I just wanted to say that you can uh
00:20:33.679 filter not just as arguments you can
00:20:36.120 filter on so many different things like
00:20:39.000 there's just endless things to filter
00:20:41.400 but like the old way to filter was
00:20:43.640 basically like you can have like
00:20:45.919 subscription and you can do like above
00:20:47.640 price you can put that in the argument
00:20:49.520 or later on you can do SUB price above
00:20:52.320 price equals 800 like you could do it
00:20:54.240 after um that's another way you could do
00:20:56.559 it and you could do like sub. um you
00:20:59.080 don't have a lot of things um you can
00:21:01.520 put here let's do like above um okay you
00:21:04.720 know let's do below price equals 1,000
00:21:08.080 okay so now let's do this um this limits
00:21:11.640 things like stocks between 800 and 1,000
00:21:14.320 so things like Nvidia so let's see how
00:21:16.640 this looks Let's uh do this method
00:21:19.640 again
00:21:24.200 um um okay so you see now the the
00:21:27.240 gappers are um are filtered by things
00:21:29.919 between $800 and $1,000 and you see
00:21:32.400 nvidia's up there o wow Nvidia was
00:21:35.760 actually like at it's crazy nid Nvidia
00:21:38.440 was like at um I think the whole Market
00:21:40.840 is going down because Nvidia was like at
00:21:42.520 906 earlier okay so now this is like the
00:21:46.360 old way of filtering and then the new
00:21:48.440 way of filtering is you have all these
00:21:50.320 like um options that like uh like you
00:21:54.000 get one to one options from the um
00:21:56.240 Market data filter and you basically uh
00:21:59.720 put all these like tags you want to see
00:22:02.080 so let me show you guys first of all
00:22:04.120 like um uh let's let's look at all the
00:22:07.200 options you can get this like XML file
00:22:10.159 and sorry I'm rushing I got like I
00:22:12.000 literally got five 5% on my phone uh
00:22:16.120 which is my internet right now so like
00:22:17.960 okay so I can do like I can run this XML
00:22:20.880 equals ib. Rec um scanner uh
00:22:26.640 parameters and uh and then if I do print
00:22:30.080 XML this will give me all the like
00:22:32.360 request scanner parameters so you get
00:22:34.600 this like nice beautiful SL ugly XML of
00:22:38.960 all the like scanner parameters I
00:22:41.520 actually saved this XML to XML file and
00:22:44.120 when it showed you guys here it's like I
00:22:46.360 did scanner parameters. XML and I
00:22:48.960 recommend you guys do that if you're if
00:22:51.039 you want to to do this um and we can
00:22:54.559 parse this XML to get like um all the
00:22:57.279 tags you can filter on
00:22:59.360 um I don't want to spend too much time
00:23:01.120 on this because like parsing XML the
00:23:03.159 best thing to do is ask Chad gbt and
00:23:05.840 struggle a little bit a lot of bit um
00:23:08.760 but let me just show you guys like the
00:23:10.200 possible tags you can filter on you can
00:23:12.600 do like import uh xml.
00:23:15.799 Tre um do element
00:23:21.000 tree um as ET and then you can do uh
00:23:25.400 tree equals et. from string
00:23:29.480 XML and this is a the way to find all
00:23:32.720 the tags uh available for filtering is
00:23:35.679 you go like abstract field code and then
00:23:38.520 this will be print the tags that you can
00:23:40.159 filter on look there's so many tags it's
00:23:43.039 just crazy you can filter on all these
00:23:45.039 things like there's things with like
00:23:47.120 sentiment uh like I can do like social
00:23:50.880 sentiment
00:23:52.760 oops uh anyways there's so many things
00:23:57.000 of P ratio after hours trade count
00:24:00.559 there's like literally endless things
00:24:02.640 you can filter on it's just insane um
00:24:05.799 and so how would you use these filters
00:24:08.039 so remember above I showed you like one
00:24:09.840 way to filter was to do like sub. above
00:24:13.279 price or to Define it in the actual um
00:24:16.600 scanner subscription so like okay so in
00:24:18.919 the scanner subscription I had filters
00:24:20.760 like above price uh things like that um
00:24:24.600 or I can later add the like dot above
00:24:26.720 price whatever but this new method with
00:24:29.440 like a billion more options what you do
00:24:32.279 is you you have these like tag values so
00:24:35.159 let me write it so like you can have
00:24:36.880 like tag
00:24:38.360 values and the tag values are from uh
00:24:41.520 like any of these options and um okay so
00:24:45.440 you you can put you put all these tag
00:24:47.159 values you can have like okay um uh
00:24:50.919 let's say there's social sentiment score
00:24:53.720 things like that um uh price above price
00:24:57.679 below uh change percent above so um the
00:25:02.080 way you would do that um and filter on
00:25:04.799 those is you would do like um uh you
00:25:07.799 would you would uh okay you could um you
00:25:11.480 would do
00:25:12.840 this so I guess uh you would do
00:25:18.039 um
00:25:20.039 um scanner subscription like last time
00:25:23.320 but now when you do ib. Rec scan data
00:25:26.240 you add um the tag values so just to
00:25:29.520 show you guys like okay the subscription
00:25:31.760 is called
00:25:33.039 subscription subcription uh the the um
00:25:37.320 second thing is uh a scanner
00:25:39.880 subscription
00:25:41.840 options
00:25:44.760 um oh okay uh
00:25:51.039 um sorry I'm not I never use this thing
00:25:54.520 so uh so uh I guess the subscription
00:25:57.320 options uh are um I think those are like
00:26:00.840 the scan codes sorry I've never used
00:26:02.760 this uh specific argument so let's just
00:26:05.120 like keep it as blank uh uh scanner uh
00:26:09.840 um subscription options equals blank and
00:26:12.320 then scanner subscription filter options
00:26:14.640 equals tag values that's the important
00:26:16.919 thing uh this was never closed I guess I
00:26:19.720 never closed it um what per is my phone
00:26:23.919 still 5% which is
00:26:25.919 good um so
00:26:30.039 let's see if this returned
00:26:32.760 anything okay so it did return
00:26:35.440 something so um let's actually uh what
00:26:38.679 we should maybe do is let's actually fix
00:26:41.080 our um our nice display method to do
00:26:44.440 that so remember we had this display
00:26:47.840 method um and then let's add a tag
00:26:52.279 values
00:26:54.080 um tag values and let's do make it none
00:26:59.720 okay and then I can do
00:27:02.960 um
00:27:04.760 um if tag
00:27:08.200 values is none then we do as
00:27:12.080 previous otherwise let's do um
00:27:16.399 else
00:27:20.679 um scan data equals ib. Rec scand data
00:27:26.080 um let's do uh this empty thing and then
00:27:28.559 um tag
00:27:30.960 values so let's see if this actually
00:27:33.720 works first time trying this thing so I
00:27:36.440 have no idea if it'll work it seems like
00:27:39.320 it it it'll still work um let me show
00:27:43.279 you guys so oh I just ran it but like
00:27:45.440 let me show you guys like again and you
00:27:47.480 know let's add a few filters just uh to
00:27:49.720 make it like um let's do uh change
00:27:54.440 percent above five 5% and let's see if
00:27:58.600 our new method works so our new method
00:28:01.480 is like
00:28:02.919 this
00:28:04.640 um let's get rid of this for a second so
00:28:07.919 let's see if our new method Works
00:28:09.840 remember here the difference is we add
00:28:12.159 tag values to our
00:28:14.039 filter um and let's uh oh sorry we never
00:28:18.480 tried this um
00:28:21.080 sorry let's keep it as is and let's make
00:28:24.200 tag values equals tag
00:28:27.120 values and let's see if this
00:28:31.440 works sub equals this
00:28:40.159 um oh okay so the only one that appeared
00:28:43.120 was wire okay um let me let's maybe make
00:28:47.039 it a little bit easier let's do percent
00:28:49.159 change above 0.1 and see if this works I
00:28:52.760 guess everything seems to be crashing
00:28:54.600 that's why uh we don't get that many
00:28:56.559 options but let's see if this works
00:28:58.720 I won't run this
00:29:00.960 one I just want to get more than one see
00:29:03.960 now we get more than one it's still
00:29:05.640 ordered by gappers that sort of thing
00:29:07.720 but the difference is now I I added the
00:29:09.960 tag values filter which gives you way
00:29:12.960 more options look at how many different
00:29:14.960 things you can filter on like it's
00:29:16.840 insane like implied volatility all this
00:29:20.080 all this good stuff institutional
00:29:22.440 ownership anyways um I don't know what
00:29:25.320 this thing does uh to be honest I have
00:29:27.279 to look that up scanner subscription
00:29:29.200 options so I'll just keep it as a list
00:29:31.279 but the filter options that's what I
00:29:32.919 said to tag values okay so now we got
00:29:35.679 this uh nice um uh data frame uh um okay
00:29:40.600 and then I just wanted to say not just
00:29:42.360 us stocks are available you have other
00:29:44.399 instruments so you can uh we can use
00:29:46.360 that XML method again the find all uh
00:29:50.080 instrument. type and we can print them
00:29:52.840 and you can see the in different
00:29:54.360 instrument types available um uh and you
00:29:58.080 see you get Hong Kong stocks US Stocks
00:30:01.720 um all these good stuff a lot of bonds
00:30:04.320 government bonds municipality bonds that
00:30:06.760 sort of thing uh sorry this was Rush CU
00:30:09.279 I literally have 3% uh battery life on
00:30:12.279 my Hotspot um anyways I hope you enjoyed
00:30:15.200 the video if you're new please like And
00:30:17.039 subscribe and I will make much more
00:30:19.960 interactive brokers IB Asing IB ins sync
00:30:22.799 videos oh and one last thing um uh if
00:30:26.720 you look at IB async or IB insync GitHub
00:30:30.159 and you look at the notebook examples uh
00:30:32.919 um a dwit the original Creator uh rest
00:30:35.600 in peace uh he has a good example on
00:30:38.120 scanners uh so like you go I've been
00:30:40.480 seeing uh notebooks uh
00:30:44.799 scanners uh and he has uh an IB an IB uh
00:30:49.720 and scanners uh he has some great
00:30:52.039 examples uh this can help you guys out
00:30:54.919 anyways I hope you enjoyed I'll put the
00:30:57.200 code up right away thank you so much and
00:31:00.279 have a great day

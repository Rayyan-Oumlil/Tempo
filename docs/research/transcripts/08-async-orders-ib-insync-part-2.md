
# tactiq.io free youtube transcript

# Incorporating Async Into Orders on Interactive Brokers API Using IB Insync (Part 2)

# https://www.youtube.com/watch/speogkirda8

00:00:01.320 [Music]
00:00:05.600 all right back for another video on IBN
00:00:09.059 sync and placing orders so I did a first
00:00:12.240 video where I did just a basic order uh
00:00:15.839 through their API was going to stop
00:00:18.060 there but I'm doing some work to try to
00:00:20.939 get this up and running and uh one of
00:00:23.640 the things that I was adding to it is
00:00:26.039 asynchronous functions and I thought
00:00:28.380 that where we left off would be a great
00:00:31.040 place to pick up and sort of show how to
00:00:33.840 implement asynchronous function
00:00:36.660 so again I'm not a computer guy so
00:00:39.620 asynchronous function is new to me if
00:00:42.239 you come over here and look at the
00:00:44.399 documentations you'll see a lot of these
00:00:47.160 codes over here that you can run and
00:00:49.680 then you see at the end of it you'll see
00:00:51.660 this async and so if you're like me
00:00:53.700 you're like what does async mean so
00:00:55.980 you'll go out and you'll look it up and
00:00:58.079 it says that you're able to basically
00:01:00.239 the code multitask so instead of buying
00:01:03.840 one share of Tesla and then buying one
00:01:05.400 share of Apple and then buying one share
00:01:06.960 whatever else it does it all at one time
00:01:09.479 it buys Apple Tesla whatever else you
00:01:11.400 tell it all at once
00:01:13.020 I'm gonna say you say okay that's great
00:01:14.760 how do I Implement that into my code and
00:01:18.360 there's not a lot of information out
00:01:20.159 there especially if you're new to coding
00:01:22.939 so what I'm going to do is I think where
00:01:25.740 we left off is a great place to pick up
00:01:27.840 and sort of show what needs to be done
00:01:30.360 to get a code like that to run
00:01:33.360 asynchronously
00:01:37.020 so let's pop back over here into the
00:01:38.880 code this is where we left off and so a
00:01:41.880 couple things right off the bat we need
00:01:43.560 to talk about the first thing is in the
00:01:46.320 first video I said that I was using
00:01:48.380 random.randint to try to randomize the
00:01:51.420 client ID to see maybe it speeds it up
00:01:53.460 and in reading the documentation you do
00:01:57.060 not want to do this because it these
00:02:00.420 orders in order to pull some of these
00:02:02.640 orders you have to be pulling it on the
00:02:06.119 same client ID that you placed it so
00:02:09.419 we always want this to be the same
00:02:11.160 number so we're going to say one there
00:02:14.160 and then the second thing is
00:02:19.080 making some initial adjustments for
00:02:21.660 asynchronous and so
00:02:24.959 first thing we're going to do is import
00:02:26.879 a sync AI
00:02:30.319 async IO excuse me import
00:02:33.680 async IO and then on the end of the devs
00:02:38.099 we're going to add async
00:02:41.280 that makes it asynchronous
00:02:46.739 all right so we're gonna
00:02:48.420 move some of this around as well what
00:02:50.340 I'm going to do is place this connection
00:02:52.379 to interactive brokers inside of a def
00:02:54.720 as well
00:02:56.099 and
00:03:04.260 say async def connect to IP
00:03:11.400 move this in there
00:03:13.280 and then uh so this is the first big
00:03:16.739 thing here that we have to change round
00:03:18.360 we can't we don't need to use IB connect
00:03:20.959 instead we're going to use
00:03:23.780 a weight IB dot connect async
00:03:30.239 and then we'll put all of this right
00:03:32.760 there on the end but instead of typing
00:03:34.860 this out what I'm going to do is I'm
00:03:36.780 going to utilize constants up here so
00:03:39.239 what I've done here is hit hashtag shift
00:03:42.480 and the number three on the keyboard
00:03:45.060 that comments it out so what I'll say is
00:03:47.400 just this is going to be the section
00:03:48.599 where we have constants
00:03:55.200 and so with these defs
00:03:58.260 um it's Supply the code Total Works
00:03:59.940 backwards right like normally the code
00:04:01.620 is reading from top to bottom but with
00:04:03.840 these defs it's sort of like a box that
00:04:06.420 you put the code into and you say I'm
00:04:08.580 not running you yet I'm just storing you
00:04:10.860 here and then whenever I need to run you
00:04:13.920 I'll refer to your name
00:04:16.918 and so the defs don't run the first
00:04:20.160 thing that runs
00:04:21.358 in this particular situation would be
00:04:23.100 this stock right here and it runs down
00:04:25.820 and so some of these codes you'll see a
00:04:28.320 lot of depths and they'll almost
00:04:31.740 everything will be deaths and then
00:04:33.360 there'll be like one line at the bottom
00:04:34.919 telling you to to run a certain death
00:04:37.740 and then inside of that death it'll run
00:04:40.680 other deaths right so it's sort of
00:04:42.540 working backwards but up here with the
00:04:44.940 constants it's not working backwards
00:04:46.500 anything we type here as a constant we
00:04:49.259 won't have to
00:04:50.900 refer or pass it through to the function
00:04:55.080 so
00:04:56.639 because it's working backwards um we
00:04:59.520 have to normally we'd have to type in
00:05:01.020 any
00:05:02.220 any variable that put down here but if
00:05:05.040 we do it as a constant up here we're not
00:05:06.840 going to have to do that so we're going
00:05:09.180 to do
00:05:13.979 it's right up here we're going to say IP
00:05:15.540 address and all of these have to be in
00:05:18.660 capital
00:05:19.800 letters and then we'll say the IP
00:05:22.800 address is going to be
00:05:24.780 one two seven I don't know if that's
00:05:26.340 exactly what it's called in the
00:05:28.139 documentation but that's why we'll say i
00:05:30.000 p address
00:05:31.199 and we'll just put this right here
00:05:38.160 we'll say port number
00:05:41.880 seven four nine six
00:05:44.759 and again
00:05:49.259 your um you'll need to make sure that
00:05:51.720 this matches inside of
00:05:54.479 Trader workstation
00:05:57.180 and talk about that in the first video
00:05:59.400 I'll leave a link
00:06:01.199 in the description
00:06:03.660 and then client ID
00:06:06.180 we're going to say one
00:06:10.500 I'll put that right there so it'll read
00:06:12.660 client ID equals client ID and so
00:06:14.820 nothing's changed here we still have the
00:06:16.560 same values but uh this will make it to
00:06:19.380 where coding a little easier
00:06:24.479 final thing we need to do is we'll need
00:06:26.160 to return IB just like that
00:06:30.960 all right so down here at the bottom uh
00:06:33.539 where we had this code that was actually
00:06:35.819 running we're going to put this into a
00:06:38.580 an async Def
00:06:40.800 we're going to call it Main
00:06:46.340 and so again like we said nothing inside
00:06:49.860 of the def's run
00:06:51.860 and so down here we're going to say to
00:06:55.620 get in order to get that main to run
00:06:57.000 initially we're going to say ace
00:06:59.039 async IO dot run
00:07:02.039 and we're going to call the main
00:07:03.960 function
00:07:05.940 other thing with a Cinco
00:07:08.120 ib.sleep doesn't work so instead of
00:07:10.560 saying ib.sleep what we're going to end
00:07:12.539 up saying is a weight
00:07:15.319 async io.sleep
00:07:18.900 foreign
00:07:20.539 back up to the top we can put some other
00:07:23.580 constants here and constants are things
00:07:25.259 that aren't going to change they're
00:07:26.699 variables that aren't going to change
00:07:28.259 during the code and so what we can do is
00:07:30.780 we can say
00:07:32.160 change equal smart
00:07:36.240 MX
00:07:38.220 and again in my experience using smart
00:07:40.860 slash Amex works on more stocks than
00:07:43.199 just smart
00:07:44.520 sometimes the smart alone doesn't
00:07:47.780 access the some of the the tickers
00:07:52.800 and then currency we can say
00:07:56.639 equal USD
00:08:00.720 so those up there I'll copy those come
00:08:03.240 down to
00:08:05.160 the place where we take the symbol and
00:08:07.500 we convert it to a the type of
00:08:10.620 formatting that ibkr wants us to have it
00:08:13.500 in and instead of having this as a
00:08:15.720 string I was pasting
00:08:17.520 the
00:08:21.180 constant
00:08:23.940 so now that we've moved some of this
00:08:25.860 stuff into their own def so we're going
00:08:27.780 to have to call it inside of these
00:08:30.660 functions
00:08:31.680 and so the first thing we want to do in
00:08:33.779 this main come down here we call it the
00:08:36.000 main so the main will run so the very
00:08:37.860 first thing we want to do is we want to
00:08:39.479 connect it to the interactive brokers so
00:08:41.820 we're going to do that by saying
00:08:44.039 IB equals
00:08:47.339 connect to IB
00:08:53.640 and then this is the difference uh when
00:08:55.920 we're calling these functions in
00:08:58.620 asynchronous we're going to type in a
00:09:02.040 weight right here if we don't do that
00:09:03.779 it's not going to actually run the uh
00:09:07.740 the function so we're going to put a
00:09:09.360 weight right there
00:09:19.019 all right so to make this as simple as
00:09:21.660 possible what we're going to be using
00:09:24.060 we're going to have two steps to this
00:09:25.800 asynchronous function the first is that
00:09:28.019 we want to package in
00:09:29.899 the symbol and the instructions
00:09:33.000 for what we want it to run and we're
00:09:34.920 going to put all of these they're called
00:09:36.959 Co routines into a list and so in this
00:09:40.260 particular example we want to run where
00:09:43.260 the ticker's at test all the tickers
00:09:46.140 let's put two tickers up here
00:09:50.399 we want to run apple and Tesla at the
00:09:54.300 same time we want to buy one share of
00:09:56.040 stock
00:09:57.660 and so what we have to do first is we
00:09:59.700 have to tell it for Apple we want it to
00:10:02.580 run
00:10:03.420 this specific code for Tesla we want to
00:10:06.240 do the specific code we're preparing the
00:10:08.700 instructions for it and then the second
00:10:10.800 step is we execute all of those
00:10:13.080 instructions at the same time and so to
00:10:15.959 start backwards here to the thing that's
00:10:18.420 going to trigger all of these to uh
00:10:22.380 cell or a buy it's a sync IO dot gather
00:10:26.940 and we're going to put star
00:10:30.360 and we're the buy task is going to be
00:10:32.399 the list where we store the instructions
00:10:36.060 and so now we have to create the
00:10:37.740 instructions and so
00:10:40.380 for me like my thinking in a typical
00:10:43.339 non-asynchronous environment what I do
00:10:45.480 is I just do a for Loop so I would say
00:10:48.180 for ticker and tickers
00:10:51.300 um
00:10:52.860 and then have this over like this the
00:10:56.640 issue here is that we're running this in
00:10:58.980 the main so what it's going to do is
00:11:00.839 it's going to cycle through so it's
00:11:02.760 going to cycle through the whatever
00:11:04.260 instructions we give it for Apple come
00:11:06.420 back to the top Give It Whatever
00:11:07.740 instructions we have for Tesla and so if
00:11:10.079 we have some code here where we're maybe
00:11:11.640 we're stopping it for a certain amount
00:11:14.100 of time
00:11:18.480 say we stop it for five seconds
00:11:21.060 it's going to start running Apple it's
00:11:23.220 going to stop for five seconds and then
00:11:25.560 it's gonna
00:11:26.640 maybe it's gonna grab that stock price
00:11:28.560 data and it's going to come back up here
00:11:30.000 and run it for Tesla and do the same
00:11:32.100 thing stop for five seconds and so by
00:11:34.260 the time we submit all these orders the
00:11:36.600 price data is going to be wrong and
00:11:39.720 you know and it's also going to be doing
00:11:41.940 it well after uh we actually run the
00:11:45.060 code so we want to move instead of doing
00:11:47.220 this we want to move all of this code
00:11:49.740 to its own separate Def
00:11:54.779 so up here
00:11:56.339 I'm going to put it right in under the
00:11:58.500 cell stock one
00:12:00.600 I'm going to call it async Def
00:12:06.480 I call it a really long one just so that
00:12:09.480 I and when I was watching understands
00:12:13.140 exactly what this is doing
00:12:15.000 so we're giving the async instructions
00:12:16.980 for the opening order
00:12:18.779 we're going to pass in IB and we'll also
00:12:21.839 pass in ticker
00:12:33.320 go ahead cut control X and then paste
00:12:36.720 control V
00:12:38.820 this code right under here and so what
00:12:40.560 we're doing is
00:12:42.480 we want this instead of saying Tesla we
00:12:44.639 want to give this ticker
00:12:51.420 and then back down here for the
00:12:53.220 instructions that we're going to do
00:12:54.899 right above that trigger we're going to
00:12:57.120 say the by tasks this is the list
00:13:00.720 that's going to contain the co-routines
00:13:04.040 we're going to say
00:13:09.360 what do we want it to do so we want it
00:13:11.579 to run the code that's under giving
00:13:14.700 async instructions for opening order
00:13:18.060 or we have to pass IV and ticker to it
00:13:21.480 and then we want to Loop through all of
00:13:24.060 the tickers
00:13:27.420 it's going to be four ticker in tickers
00:13:30.180 ticker is just a made up variable
00:13:32.940 tickers up here is the one where we've
00:13:35.339 given it all the the tickers and so
00:13:38.279 ticker is going to have
00:13:40.139 it's going to run through a for Loop and
00:13:42.540 for each cycle it's going to have a
00:13:44.940 ticker so the first cycle ticker is
00:13:48.360 going to be apple and second one's going
00:13:50.459 to be Tesla
00:13:55.980 all right so before we create these
00:13:57.779 instructions I'm going to move this
00:13:59.639 around a little bit I'm going to give
00:14:01.440 all of these their own Des so up here
00:14:04.139 I'm going to say async TEF and what this
00:14:07.680 is doing is we're taking the symbol of
00:14:10.560 AAPL and we're formatting it the way
00:14:13.200 that interactive brokers needs to be
00:14:15.060 formatted in order to read it so I'm
00:14:17.040 going to say
00:14:18.000 um
00:14:19.620 I'll call this formatting symbol
00:14:24.360 for IV KR
00:14:28.980 and then we'll just paste cut this
00:14:32.700 put this up here
00:14:38.040 we'll have to give that ticker
00:14:41.639 and then right down here as place what
00:14:44.519 we'll say
00:14:46.380 is
00:14:49.079 what are we returning here we're
00:14:50.699 returning
00:14:51.899 stock
00:14:53.699 and stock holds the properly formatted
00:14:57.660 thing and so we want stock here and
00:15:00.120 we're going to say equals formatting
00:15:02.760 symbol
00:15:04.680 pass ticker to it
00:15:06.899 and then
00:15:08.100 remember easy to forget in this async
00:15:13.079 environment we have to put a weight
00:15:14.279 right here
00:15:17.820 second one I'm going to do right up here
00:15:19.980 so we're going to say diff
00:15:22.740 um
00:15:24.300 kind of an async excuse me
00:15:28.380 connecting to
00:15:31.639 ibkr kind of data say say stock data
00:15:36.660 and you can give these whatever name you
00:15:38.339 want
00:15:39.899 connecting to stock data ibkr
00:15:45.660 and we'll cut this put it right here
00:15:50.220 what do we have to give this we'll have
00:15:51.899 to give it
00:15:53.339 the properly formatted stock that we had
00:15:55.980 up here
00:15:57.600 we'll say stock right there
00:15:59.699 and we also need to give it IB
00:16:05.579 so we can return this data here and I'll
00:16:08.339 go ahead and run it and print the data
00:16:10.079 sort of show
00:16:12.360 how it's formatted
00:16:15.360 so down here we'll say data
00:16:17.639 equals
00:16:19.800 connecting to IV KR
00:16:22.380 and what did we pass it we passed the
00:16:24.300 ibane stock
00:16:27.079 and then we'll print the data
00:16:30.600 and then we'll so I'll run the code and
00:16:32.760 I'll stop it right here so we'll come
00:16:34.079 over here in Visual Studio code we'll
00:16:35.820 set a breakpoint right there
00:16:37.620 and then we'll set a break point right
00:16:39.180 down here as well
00:16:40.620 and we'll come down to the fourth Tab
00:16:42.540 and run to debug
00:16:58.199 okay looks like I didn't properly add I
00:17:01.019 must have uh
00:17:02.820 kind of confused up here and explaining
00:17:04.740 the constants so we want this to go
00:17:06.780 inside of the connect async so we can
00:17:09.720 get rid of that IV connect
00:17:11.760 okay so there we go so that should work
00:17:23.819 all right so I'm gonna go ahead and go
00:17:26.040 forward there
00:17:29.100 all right so you see down here it said
00:17:30.840 Co routine object and so again I didn't
00:17:33.240 put a weight so we'll put a weight there
00:17:35.700 I'll run this again
00:17:50.640 all right so you can see down here it
00:17:52.080 says ticker and what this is right here
00:17:55.140 is is this uh beginning with stock right
00:17:57.840 down here is the format that ibkr wants
00:18:02.520 it in so if you just give it AAPL it's
00:18:05.580 not going to understand what you're
00:18:06.480 saying that's what we did up here when
00:18:09.179 we formatted symbol for ibkr but there's
00:18:11.880 no data and so one of the things we have
00:18:14.220 to do here is we have to give it some
00:18:16.200 wait time to load because it says that
00:18:18.660 if you don't provide any wait time it's
00:18:21.600 not going to load in so I'm going to say
00:18:23.039 it
00:18:23.820 uh await asyncio.sleep we'll give it
00:18:26.760 just a quarter second
00:18:31.080 and then that should be good so let's go
00:18:33.179 ahead and do that again
00:18:35.520 all right so you can see down here the
00:18:37.200 data is loaded in and uh you can see we
00:18:40.260 can get the bid price we can get the ask
00:18:43.140 price and get the last and we can get
00:18:46.500 the close and so one of the things
00:18:48.780 you'll notice when working with this
00:18:50.880 data is that they completely turn off
00:18:53.460 the bid in the ask for many symbols
00:18:56.700 during when the Market's not open so if
00:18:59.520 you're you know in the evenings trying
00:19:01.140 to work on code and get it up and
00:19:03.960 running
00:19:04.940 you'll have to use
00:19:08.520 close if available sometimes they don't
00:19:10.860 make any data available at all typically
00:19:13.559 though with apple and Tesla you will get
00:19:16.260 some data in the the close value at all
00:19:19.740 times so what we're going to do is uh
00:19:22.919 right under this weight we're going to
00:19:25.860 Define all of those values so we're
00:19:28.320 going to say stock ask equals
00:19:31.740 and then so how to obtain that
00:19:35.059 bid mask so
00:19:38.520 we're going to say data up here I'm
00:19:40.559 going to change this to stock data I
00:19:42.299 think would probably be more
00:19:45.240 better term
00:19:47.760 so change that return to stock data
00:19:52.020 and we'll say stock data
00:19:54.539 dot ask
00:19:59.820 when reading this return all of these
00:20:02.160 little equal signs here whatever's to
00:20:04.380 the left of it you can access by just
00:20:06.660 doing Dot ask or dot uh whatever the
00:20:09.120 name of it is so if we wanted to access
00:20:10.919 the contract we would say dot contract
00:20:13.020 we wanted to access
00:20:17.100 time we would say that time it would
00:20:19.020 turn in date time so we're going to do
00:20:20.700 that for all of these the bid the ask
00:20:22.580 the last and the close so I'm going to
00:20:25.679 do that and pick back up I'm done
00:20:28.620 all right so I've entered all those and
00:20:30.480 done a print statement right down there
00:20:31.980 and so we'll return all of these
00:20:36.600 right down here at the very last
00:20:38.100 statement so stock ask stock bid
00:20:41.340 stock last
00:20:43.440 stock close
00:20:51.120 thank you
00:20:52.679 all right so we've connected to we've
00:20:54.780 formatted the symbol and then we connect
00:20:56.400 use that connect to the stock data now
00:20:59.160 that we've got the stock data we want to
00:21:00.480 set the limit price and so we're going
00:21:01.919 to say limit price equals and I'm going
00:21:04.500 to use the close because I know that
00:21:06.240 works Around the Clock
00:21:12.660 on the stock close I'm going to do
00:21:15.179 -1 because just for example purposes
00:21:17.220 because I don't actually want these to
00:21:18.720 fill
00:21:21.480 and
00:21:24.660 then our final step is to actually buy
00:21:27.720 the stock so we're going to say
00:21:30.120 await buy stock make sure that's what we
00:21:33.299 named it up here yeah buy stock
00:21:36.000 and what we're going to end up passing
00:21:37.500 into that because we come up here you'll
00:21:39.299 see that we've got some errors up here
00:21:41.400 so we have to pass into it IB
00:21:45.780 we also have to pass
00:21:48.179 properly formatted
00:21:50.220 stock that IB will read and then we also
00:21:53.580 need to pass in the limit price
00:21:56.220 and down here what we did
00:21:59.179 data.ask we'll just make this limit
00:22:01.320 price
00:22:02.940 same thing for the sell side
00:22:16.440 and then we need to return
00:22:20.700 oops
00:22:22.500 turn
00:22:24.780 order
00:22:40.020 so this is where we're buying the stock
00:22:42.179 now so I'm going to get rid of some of
00:22:43.860 this
00:22:44.760 stuff down here that was from the old
00:22:47.580 code so what we're doing here
00:22:51.539 connected to interactive brokers we've
00:22:54.360 given it the asynchronous instructions
00:22:56.700 right here we've told it here are the
00:22:58.620 instructions you need do this for Loop
00:23:01.200 through and and set these instructions
00:23:03.179 for every single ticker in our ticker
00:23:04.980 list and then we actually execute
00:23:07.679 buy stock
00:23:12.780 then the very final command we're going
00:23:14.640 to give it is
00:23:19.740 IV that disconnect
00:23:24.720 all right so we can go ahead and run
00:23:26.159 this and
00:23:27.900 pop open the
00:23:37.679 interactive brokerage workstation so we
00:23:39.900 can see
00:23:41.039 when it runs
00:23:42.659 go ahead and run it
00:23:45.840 and there we go instantaneously it put
00:23:48.600 apple and Tesla there
00:23:54.299 so to highlight the multitasking and
00:23:56.700 sort of show what it's doing I'm going
00:23:58.679 to crank this up from a quarter second
00:24:00.960 to five seconds and we're going to add
00:24:02.960 some more tickers up here
00:24:11.400 when we run this we should see that
00:24:13.679 it'll wait five seconds
00:24:15.780 and then it'll it'll put an order for
00:24:17.940 all four of those so we're not doing a
00:24:21.059 loo a for Loop where we're waiting five
00:24:23.039 seconds placing one waiting five seconds
00:24:24.900 placing another one instead we're just
00:24:27.240 running this code for all four of them
00:24:29.640 all at the same time so they're all
00:24:31.140 going to get to this sleep at the same
00:24:34.020 time they're gonna all sleep at the same
00:24:36.179 five seconds and they're all going to
00:24:37.679 place their orders and we're only
00:24:39.480 waiting five seconds or whatever we
00:24:42.480 specify rather than 20 seconds
00:24:46.919 so let's observe it over here on the
00:24:50.280 terminal first I'll see that it's
00:24:53.400 connected to interactive brokers
00:24:56.880 and then it just printed all of our
00:24:59.340 prices all at the same time
00:25:02.700 and then we can observe it happening
00:25:04.559 over here Trader workstation they all
00:25:06.539 came in at the same time
00:25:09.179 so now we've got them working where
00:25:11.100 they're placing the order to get them to
00:25:13.200 sell after 15 seconds like we did in the
00:25:15.960 other code we'll come out here and first
00:25:17.520 we'll say await
00:25:21.299 15 seconds
00:25:22.980 and then we'll want to place a cell
00:25:25.980 in order to sell all those
00:25:28.140 so I'll copy in this right here and say
00:25:31.020 cell tasks instead of buy tasks
00:25:34.380 and what we're going to do is we're
00:25:36.120 going to come up here and copy this
00:25:37.620 these instructions
00:25:39.840 and paste them into a new
00:25:42.720 def we're going to change the name of
00:25:45.360 this though instead of giving async
00:25:47.520 instructions for opening order
00:25:52.020 we're going to say closing order
00:26:01.020 I'm going to change this to plus one
00:26:02.760 again you won't have this here this is
00:26:05.700 just to make sure they don't actually
00:26:06.720 fill
00:26:07.860 uh I'm on a paper account though so I
00:26:10.140 could go ahead and have them fill but uh
00:26:13.860 leave that for time being and then we'll
00:26:15.600 say sell stock right there
00:26:18.240 and so we'll come down here we'll change
00:26:20.100 this again to cell tasks
00:26:23.159 and change this to closing
00:26:29.760 all right so we'll go ahead and give
00:26:30.900 this a run and we should see it wait for
00:26:32.520 15 seconds and then put sell orders in
00:26:35.100 for those buy orders
00:26:38.460 all right so I'm looking down the list
00:26:40.620 here it looks like it's returning prices
00:26:42.779 for all of all four of these stocks so
00:26:46.100 I'm going to change this what we want to
00:26:48.840 to simulate a market order in the the
00:26:51.659 pre-market hour again we're at seven 36
00:26:54.779 a.m so
00:26:56.720 to simulate we can only place limit
00:26:59.580 orders in the pre-market so to simulate
00:27:02.340 a market order where we'll get filled
00:27:03.960 immediately
00:27:05.159 what we'll do is
00:27:06.840 um prefer the closing or selling so
00:27:09.720 we'll say stop bid
00:27:12.059 and then up here when we're buying we'll
00:27:13.980 say stock ask
00:27:17.760 all right so for the grand finale let's
00:27:19.799 go ahead and run this
00:27:22.919 and it's connecting
00:27:27.480 just placed all those orders and we got
00:27:29.220 filled on all of them immediately
00:27:34.500 and now we're in the process of waiting
00:27:36.120 15 seconds
00:27:38.220 I should Place those sell orders
00:27:46.860 and place the sell orders and they're
00:27:48.720 getting filled and they all filled
00:27:52.080 all right so to just highlight one last
00:27:53.880 thing I've gone ahead and run the code
00:27:55.980 here
00:27:59.159 and what you can see is we have these
00:28:01.140 open orders but they're not filling and
00:28:03.659 so this highlights one issue where we
00:28:06.539 have to sell orders coming up but we
00:28:08.580 haven't been filled so we're gonna now
00:28:11.220 place the sell orders and but we don't
00:28:13.679 really want them to be placed because we
00:28:15.659 never got filled in the first place and
00:28:18.720 so we get this warning message and we're
00:28:20.880 now short all of these stocks when we
00:28:24.539 really just wanted to close out of it so
00:28:26.220 we need to add on something that is
00:28:29.340 where it observed after that 15 seconds
00:28:31.620 instead of just blindly placing sell
00:28:33.840 orders it comes in and it looks at the
00:28:36.419 open
00:28:37.500 it says which ones are open and which
00:28:39.840 ones have not been filled yet and if the
00:28:42.240 stock has not been filled then it won't
00:28:45.659 place that sell order and so we'll talk
00:28:47.820 about that in another video

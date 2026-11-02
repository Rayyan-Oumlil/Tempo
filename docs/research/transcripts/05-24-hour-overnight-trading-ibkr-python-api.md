
# tactiq.io free youtube transcript

# 24 Hour Overnight Stock Trading with Interactive Brokers Python API

# https://www.youtube.com/watch/clTsKB7Uac4

00:00:00.240 So for trading addicts, obviously
00:00:02.080 regular trading hours are not enough.
00:00:04.480 Pre-market and after hours are not
00:00:06.480 enough. So brokerages like Robin Hood
00:00:08.800 and Interactive Brokers introduced
00:00:10.880 overnight 24-hour trading. So you can
00:00:13.679 trade 24 hours a day, basically Sunday
00:00:16.400 evening through Friday Eastern. Um
00:00:19.600 except maybe a 10-minute gap in between.
00:00:21.840 Uh but basically you can trade all hours
00:00:24.720 a day. It's called the overnight market.
00:00:26.400 As you see, um, after hours are closed,
00:00:29.359 but, um, you see Alibaba's price
00:00:31.199 overnight. It's, uh, it was actually up
00:00:33.440 to almost 120. Now it's up 87 overnight.
00:00:36.960 So, what's cool about this video is I'm
00:00:38.879 going to show you that with Interactive
00:00:40.160 Brokers API, you can actually get market
00:00:43.120 data, so real time data overnight. You
00:00:45.760 can get historical data and you can make
00:00:49.280 uh, orders overnight. So, you can use
00:00:51.840 the API. You don't need to just gamble
00:00:54.239 um, uh, manually. you can actually use
00:00:56.640 API and that sort of thing. Of course,
00:00:59.280 you should be careful overnight. There's
00:01:00.879 way less liquidity, that sort of thing.
00:01:03.120 But maybe for Alibaba that's traded in
00:01:05.199 Hong Kong exchange, there's actually a
00:01:06.960 lot of liquidity uh because it has to
00:01:09.520 match the Hong Kong price or there's
00:01:11.119 arbitrage. But anyways, let's jump in
00:01:13.600 and get started. So, first thing is
00:01:15.439 we're going to use IBA async, which is
00:01:17.280 the maintained version of IB Insync. So
00:01:19.680 we're going to do u so you try you log
00:01:21.920 into IB gateway of course uh uh and
00:01:25.280 after that you do from IBA async import
00:01:28.320 star
00:01:29.840 you do IB equals IB you do util start
00:01:33.200 loop for Jupyter notebooks and then you
00:01:35.840 do IB connect portals 40001 client ID
00:01:40.960 equals zero for example so you connect
00:01:43.600 to uh IB so the the big picture thing in
00:01:47.759 the API let me just make this full
00:01:49.439 screen. The big picture thing, what's
00:01:51.920 important is um when you're defining a
00:01:55.439 contract, you have to use exchange
00:01:57.840 equals overnight. If you use exchange
00:02:00.320 equals overnight, then everything works
00:02:03.680 as you expect. So, for example, let's
00:02:06.479 use Alibaba because that is heavily
00:02:09.280 traded uh overnight just because it has
00:02:11.680 Hong Kong exchange. So, the Hong Kong so
00:02:14.400 so it's like it moves overnight. So I'll
00:02:16.879 do stock equals uh um symbol equals baba
00:02:22.000 and the key thing here now is I write
00:02:24.080 exchange equals overnight
00:02:27.599 and I think this might be enough to
00:02:30.640 qualify the contract. So if I do
00:02:32.720 IB.qualify contracts stock
00:02:36.560 um it uniquely identifies the contract
00:02:39.680 uh it gives all the other things primary
00:02:41.519 exchange overnight currency all that
00:02:44.000 good stuff. So now uh we have our
00:02:46.480 contract. So the key thing of course is
00:02:49.360 exchange equals overnight. So now we can
00:02:52.480 subscribe to live market data. So I can
00:02:54.879 do um ticker equals ib.rec Wreck market
00:02:59.280 data
00:03:01.200 uh oops wreck
00:03:03.840 uh market data uh stock this thing false
00:03:09.599 for the snapshot
00:03:12.000 and false for be best bid ask. So now I
00:03:15.440 I have the ticker object. So I can do
00:03:17.519 ticker bid ticker ask ticker midpoint uh
00:03:22.640 ticker doarket price for example.
00:03:25.920 So this is cool because like you have
00:03:27.760 the real market data. So you see these
00:03:29.760 numbers 17.63 17 uh.73 117.73 117.68
00:03:36.159 117.67. You click it again the numbers
00:03:38.799 change. As you see the last one changed
00:03:40.400 to 64. We can of course use callbacks.
00:03:43.040 You could do defaf on ticker update
00:03:46.480 ticker and then we can print the same
00:03:48.959 thing just to make it a little bit like
00:03:51.599 uh to review callbacks for some of you
00:03:53.920 guys uh who uh don't use this API every
00:03:57.200 second. So we can print this and then we
00:04:00.000 can of course do ib uh we can do
00:04:03.040 ticker.update
00:04:04.720 event plus equals on ticker update and
00:04:08.879 then I can do ib.sleep sleep 10 just cuz
00:04:11.920 I I want to print it for 10 seconds and
00:04:13.760 then I'm going to clear the um callback
00:04:16.639 clear and let's see if this worked. So
00:04:19.440 um as you see like every uh it's
00:04:22.400 updating the ticker. Unfortunately there
00:04:24.880 wasn't a change in this example. So uh
00:04:28.400 anyways that finished. Let's try to get
00:04:30.880 a change in. It's okay. See as you see
00:04:33.680 there's changes here. So as you see you
00:04:36.479 can use callbacks. I did IB that sleeps
00:04:38.320 to make it run only for 10 seconds. Uh,
00:04:41.199 and now it it finishes. You can also
00:04:43.840 stream real time bars. So 5-second bars.
00:04:46.720 So I can do live bars equals IB.rec
00:04:51.360 realtime bars. Uh, is this big enough
00:04:54.639 the font?
00:04:56.560 Okay. I hope the font is big enough. Uh,
00:04:58.880 leave a comment if you want the font to
00:05:00.800 be bigger. So I can do stock. Um, I can
00:05:04.080 do uh what do I need? I need uh contract
00:05:07.039 equals stock. Bar size is always five
00:05:09.759 seconds. I don't even know why they have
00:05:11.440 that argument. Uh what to show? We'll
00:05:14.320 show trades.
00:05:16.639 And what else do we need? We need uh use
00:05:19.280 regular trading hours. You need to write
00:05:20.880 false here. And what else do I need? Uh
00:05:23.440 I think that's everything, right? Uh
00:05:25.759 okay. So these are live bars. And as you
00:05:28.240 see, these are the live 5-second bars
00:05:30.160 that keep updating. So if I keep
00:05:31.840 clicking it, it's going to update uh and
00:05:34.479 keep adding to it. uh every 5 seconds is
00:05:36.960 going to be a new bar and you can use
00:05:38.800 callbacks also. So I can do defaf on new
00:05:41.840 bars
00:05:44.320 has new bar and it always has a new bar
00:05:47.680 when it's uh 5-second bars. So I can
00:05:50.400 just do print uh uh let's say uh new bar
00:05:55.120 and then I'll print the last bar. So
00:05:56.880 I'll do uh print bars minus one. I'm
00:06:00.160 just showing you like how you could do
00:06:01.280 the call back here to remind you guys.
00:06:03.440 So live bars do update event plus equals
00:06:07.440 on uh I called it on on new bar but we
00:06:11.280 can just make it on new bar. Okay. So
00:06:13.759 now if we uh we could do the same thing
00:06:16.400 uh we could do ib.sleep
00:06:18.880 10 just so we after 10 seconds we're
00:06:21.600 going to clear it. Live bars
00:06:24.880 update event. And let's see if this
00:06:27.759 works.
00:06:29.280 So um we expect every new bar it's going
00:06:32.639 to print new bar and give you the
00:06:34.000 real-time bars. So like the time the uh
00:06:37.440 open high low close volume and this is
00:06:40.560 of course for overnight trading. Okay.
00:06:42.960 And what's cool is you can also get
00:06:44.479 historical bars. So I can do historic
00:06:47.120 historical bars equals ib.rec wreck
00:06:51.039 uh wreck his historical
00:06:55.600 historical uh uh data and what do I
00:06:59.440 need? I need the contract. So stock and
00:07:01.840 date time I can just use this duration
00:07:04.479 string. Let's do uh 300 seconds. Uh and
00:07:08.880 what to show? Let's show trades. Uh and
00:07:13.360 what else do I need? Uh use regular
00:07:15.919 trading hours equals false. And what I
00:07:19.440 think that's enough. Uh, oops. Oh, sorry
00:07:24.240 guys. What to show equals trades. Uh, is
00:07:27.680 this good? Uh, bar size setting.
00:07:31.599 What did I miss? Uh, oh, what type of
00:07:34.479 bar we're going to use? Bar size
00:07:36.000 setting. Let's do 5-second bars also.
00:07:38.000 Okay. So, what do I miss? Uh
00:07:51.680 oh. Sorry guys. I needed to do this. I'm
00:07:54.879 rusty. Uh uh I never uh the funny thing
00:07:59.599 is I actually never use um I never use
00:08:03.759 uh Interactive Brokers for market data
00:08:06.639 uh lately. So I'm a little rusty with
00:08:09.360 this. So now I have historic and I and I
00:08:11.520 also don't use bars anymore. I only use
00:08:13.280 uh tick data. So historical bars uh here
00:08:17.599 uh it worked uh after I fixed some
00:08:19.759 settings. Util.df historical bars works.
00:08:23.840 And as you see uh you get like uh the
00:08:26.879 the latest uh things. Let's just uh you
00:08:30.319 get the latest things. Uh 117.5.
00:08:33.200 And if I keep uh updating uh these
00:08:35.599 things, you'll see it'll keep updating.
00:08:37.440 So 117.5
00:08:39.679 uh up to 50 seconds, right? And I and I
00:08:43.679 think you can also do keep up the date
00:08:45.279 is true. Uh does that work?
00:08:49.279 So now uh as you see I have um up to uh
00:08:54.000 uh 20 5550 because I have keep up to
00:08:57.440 date and let's see if this works. 2056.
00:09:01.680 See it works. It keeps it up to date. So
00:09:04.080 that's pretty cool. So even for
00:09:05.760 overnight data you can keep up to date
00:09:07.440 is true. Uh and now this is the fun part
00:09:10.160 and this is a real account so I got to
00:09:12.240 be careful uh placing overnight orders.
00:09:15.040 So you can place overnight orders. Uh as
00:09:17.600 you see Baba cooled down a little bit.
00:09:19.920 You know what just for fun I'm I'm okay
00:09:22.080 with buying a 100 shares at 117. So
00:09:25.360 first of all let me make sure I have no
00:09:26.720 open orders. Uh I have no open orders.
00:09:30.399 Okay just to show you guys this works.
00:09:32.399 Second thing is um for this to work you
00:09:34.880 have to uh make sure there's another
00:09:37.040 thing you have to do uh if I ever figure
00:09:39.760 it out. One second. You have to go to
00:09:41.839 the IB gateway and you have to uh click
00:09:45.360 on uh basically you have to click on
00:09:48.000 configure settings uh precautions and
00:09:52.240 you need to do bypass redirect order
00:09:55.120 warning for stock API orders. You might
00:09:57.839 also need to do bypass order conditions
00:09:59.920 for API orders. But this for sure you
00:10:02.080 have to do bypass redirect order warning
00:10:04.399 for stock API orders. So you do that in
00:10:07.440 IB gateway and then it should work. And
00:10:09.360 let me just make sure I don't cuz this
00:10:11.360 is a real trade. I don't if it's at 117
00:10:13.760 I'll live with that. Um it'll be a real
00:10:16.800 trade at 117. So as you see I have no
00:10:19.360 orders but I could do IB.P place order
00:10:22.800 uh stock limit order and then I can do
00:10:26.079 buy and then I can do let's say 100
00:10:29.279 shares and my limit price is 117. So now
00:10:33.519 I I I place this order. I guess I should
00:10:35.920 have saved it. Uh let me cancel it for a
00:10:38.560 second. IB do um cancel and I got to
00:10:42.959 make sure I I didn't mess up. So I could
00:10:45.279 do order just to remind you guys. You
00:10:47.519 can do four order in IB.open orders
00:10:55.680 IB.Canc order like that. Um, but let's
00:10:59.279 say I I I place this order. I can call
00:11:02.079 it trade.
00:11:03.920 Uh, let's see. No orders because I
00:11:05.920 canceled order here. I place this order
00:11:08.399 trade. And let's look at the order
00:11:10.320 status. I could have accidentally got a
00:11:12.640 fill if Alibaba dropped, but uh we'll
00:11:16.160 check that in a second. Tra I could do
00:11:18.640 IB.fills. Uh but it might have
00:11:20.399 yesterday's stuff. I had a million
00:11:22.320 trades yesterday. So uh yeah, I think it
00:11:26.000 has all my trades from yesterday. So uh
00:11:29.120 this is a real account, so like I got to
00:11:31.519 be careful. So like Okay. So I did place
00:11:34.079 a trade again here. And let's look at uh
00:11:36.560 you can trade the order. Uh oops. Why is
00:11:40.800 this freezing on me? Uh, so this is the
00:11:42.880 order 117. We can also do trade order
00:11:45.600 status, of course.
00:11:47.760 And as you see,
00:11:50.560 froze.
00:11:53.440 As you see, it was submitted. So, this
00:11:55.200 is a real order. So, if Alibaba goes
00:11:57.680 under 117, I accidentally bought 100
00:12:00.880 shares. Anyways, I hope you guys enjoyed
00:12:03.200 this video. If you're new, please like
00:12:04.800 and subscribe. Same disclaimer as
00:12:06.959 always. Uh and have a amazing night,
00:12:10.160 day, wherever you

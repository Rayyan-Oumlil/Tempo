
# tactiq.io free youtube transcript

# The ultimate Interactive Brokers API Tutorial Part 1

# https://www.youtube.com/watch/_AASJZyNcXQ

00:00:00.640 Hello everyone. So, this will be a very
00:00:03.520 detailed two-part series on algo trading
00:00:06.200 with Interactive Brokers with the IB
00:00:08.720 Async API. It was once known as IB
00:00:11.680 Async. Um, this is going to be very
00:00:14.200 comprehensive. In the first video, we're
00:00:16.440 going to be talking about like
00:00:18.120 contracts, like stocks, options, forex,
00:00:22.160 combo contracts, and then we're going to
00:00:24.840 talk about like um
00:00:26.840 looking at your account summary, account
00:00:28.800 information, uh your positions.
00:00:32.119 Then I'm going to talk to you about
00:00:33.280 placing orders, and then we're going to
00:00:35.720 show you how to get like um data,
00:00:38.120 getting live market data, and bar data,
00:00:40.720 and that sort of thing. And in the next
00:00:42.720 video, we're going to really show you
00:00:44.480 how to create trading systems uh fully
00:00:47.080 utilizing the as the name suggests the
00:00:49.280 asynchronous uh format um and the
00:00:52.720 event-driven format, which is amazing.
00:00:55.160 So, um hopefully you like this video. If
00:00:57.280 you're new, please like and subscribe. I
00:00:59.400 have like maybe 30 or 40 videos on
00:01:01.680 Interactive Brokers. So, um um it's very
00:01:05.560 useful for some people, especially
00:01:07.240 beginners. So, hope you enjoy it, and
00:01:09.320 let's let's just get started. Okay. So,
00:01:12.240 there's two big ways to connect to
00:01:14.320 Interactive Brokers API. Um, you need to
00:01:17.240 either use Trader Workstation or IB
00:01:19.560 Gateway. So, Trader Workstation is a
00:01:22.280 fully blown like kind of like a
00:01:24.920 TradingView application or Thinkorswim,
00:01:27.960 but it also you could connect to um to
00:01:31.480 the API with that. So, just um you can
00:01:34.880 you can do that. I don't want to show
00:01:36.240 you that because it's like heavyweight.
00:01:37.840 It has graphs. It has bulletin news.
00:01:40.640 It's a huge Java thing. Um, and but I
00:01:43.960 will make another video on it because
00:01:45.760 the only thing There are things you can
00:01:47.520 only do with Trader Workstation that you
00:01:49.680 can't do with um IB Gateway. IB Gateway
00:01:53.720 um is the way I recommend to log in
00:01:56.000 because it's lightweight. There's no
00:01:57.920 like graphs or pretty things. It's just
00:02:00.480 connecting, and that's it. So, you can
00:02:02.560 Google IB Gateway, and then press
00:02:04.120 download. And then when you you do that,
00:02:06.760 you go to like IB
00:02:10.160 IB Gateway.
00:02:11.840 Okay.
00:02:12.800 So, now you get IB Gateway, and then you
00:02:14.760 can sign in to live or paper trading.
00:02:17.080 One very important thing is make sure
00:02:19.560 your time zone is what you expect. I for
00:02:22.400 the longest time had a bug in my code
00:02:24.520 because I put a wrong time zone. So, now
00:02:27.960 as a default, I always make sure I have
00:02:29.800 America, New York, but be careful. Uh it
00:02:34.240 always puts it to whatever time zone
00:02:36.280 you're at, I think, by default. Change
00:02:38.480 it to make sure you know what it's in
00:02:40.880 the right time zone that you expect.
00:02:42.880 It's very important um tip. Okay. So,
00:02:46.280 now you log in.
00:02:47.920 So, let me log in without showing you my
00:02:49.560 credentials for a second.
00:02:54.480 So, now I'm logging in. Okay.
00:02:56.840 So, um
00:02:58.480 first things first is there's like
00:03:00.240 settings, and then there's API settings.
00:03:04.520 Um, you have like a socket you connect
00:03:06.800 to, like which um
00:03:08.600 port. So, here's 4004.
00:03:11.320 Uh you can configure that. And the
00:03:13.080 important one more important thing is
00:03:14.840 it'll warn you about the read-only API.
00:03:17.000 I think it by default it's like this,
00:03:19.640 and you probably should keep it like
00:03:21.120 this uh so you won't accidentally place
00:03:23.760 orders. But anyways, um
00:03:25.880 the other small important thing that
00:03:27.480 I'll talk about later is there's like
00:03:28.760 this client ID um
00:03:31.600 uh master client ID cuz like
00:03:34.760 you also log in with a client ID, and
00:03:36.640 they don't see each other's orders or
00:03:39.160 open orders. So, if you have a master
00:03:41.240 client ID, it sees everyone's open
00:03:43.480 order, but there's also a special client
00:03:45.800 ID called zero, where you can see orders
00:03:48.960 you make with your phone. So, I'll talk
00:03:50.960 about that at the end. But anyways,
00:03:52.880 there's a lot of precautions and
00:03:54.280 settings. I don't want to get into that.
00:03:56.560 Um, just uh make sure uh some of the
00:03:59.360 time zones things uh uh make sense, like
00:04:02.440 makes it like instrument time zone. Make
00:04:05.240 sure it's it's it does what you expect.
00:04:08.240 Make sure your time zones are lined up.
00:04:09.920 That's a very important tip. Um
00:04:13.120 So, okay. So, one more thing is there's
00:04:15.520 like a lock and exit, and I have another
00:04:17.880 video talks about that because
00:04:19.480 automatically it will log you off once a
00:04:21.959 day or restart you once a day, and you
00:04:24.680 can set what time to do that. So, um I
00:04:27.480 have another video that talks about
00:04:28.920 that. Um And I have it actually here.
00:04:32.200 Um, so uh later we'll we'll talk about
00:04:34.760 that. Um, I mean, you can see the video
00:04:37.680 cuz I'm going to put this on GitHub.
00:04:39.320 Okay. So, now let's talk about the
00:04:41.440 open-source package, the IB Async
00:04:43.880 {slash} IB Async. So, there is a
00:04:47.240 an amazing amazing amazing computer
00:04:49.960 programmer, Ilwaldy Wit. Unfortunately,
00:04:52.560 he passed away. Um, he's amazing not
00:04:55.120 just because of Interactive Brokers, by
00:04:56.840 the way. Um, he also has a lot of other
00:04:59.600 amazing packages that are used in in
00:05:02.400 other areas. Um, so just real quick, um
00:05:05.960 he created this like IB Async package,
00:05:09.440 um and it was amazing.
00:05:11.600 Um, and then unfortunately, uh he um
00:05:16.400 he passed away suddenly March 11th. So,
00:05:19.960 it was really sad. People didn't know
00:05:21.520 what to do, but like so many people were
00:05:24.240 using this library, and they had to like
00:05:25.840 this amazing uh groups uh uh group
00:05:29.240 thing.
00:05:30.160 Uh so, they decided to like keep it
00:05:32.120 strong, and there's tons of people using
00:05:34.160 the library, so it'll keep going. Uh you
00:05:37.680 I I wouldn't worry about it stopping
00:05:39.280 anytime soon. So, they re um did it in
00:05:43.040 this IB Async thing. So, uh Matt uh
00:05:47.080 leads this thing, and there's a few
00:05:49.160 other people that um contribute and uh
00:05:52.240 out with things. And um there's there's
00:05:55.080 a lot of there is new uh groups and
00:05:57.200 Discords uh and that sort of thing. Um
00:06:00.360 So, uh like Clim Ermel is an example. Um
00:06:02.960 so, uh um when I get more information
00:06:06.320 about these things, um I can uh try to
00:06:09.160 put it on thing. But anyways, I wouldn't
00:06:11.360 worry anytime soon about this library uh
00:06:13.600 not working. So, anyways, um
00:06:16.880 uh you can install the library. Let's
00:06:18.800 use the IB Async. You just do pip
00:06:21.320 install
00:06:23.120 install IB Async. Okay.
00:06:25.520 Okay. So, the first step uh
00:06:28.040 is you need to connect to Interactive
00:06:29.520 Brokers. So, you have to do from IB
00:06:32.480 Async import star. And if you're using
00:06:35.600 IB Async, you just switch this to IB
00:06:37.720 Async. Then you have to do this
00:06:39.840 util.start_loop.
00:06:41.600 And what this util.start_loop does, if
00:06:43.720 you guys want to be nerdy, is it it does
00:06:46.360 nest asyncio uh nest asyncio. So, it it
00:06:50.760 makes sure you can have like an event
00:06:52.760 loop within an event loop. And also,
00:06:55.080 this is a package that Ilwaldy Wit
00:06:56.640 created. So, um that's really cool, but
00:06:59.920 um he wraps it in this util.start_loop.
00:07:02.920 So, we connect. Remember, my port was
00:07:04.680 4004, and let's use client ID equals uh
00:07:08.560 zero. Okay.
00:07:10.280 So, I'm connected. Okay. So, the first
00:07:12.480 thing you need to know is about
00:07:13.760 contracts. Contracts are basic things
00:07:16.120 like stocks, options, uh that sort of
00:07:18.440 thing. So, you can define a contract
00:07:20.760 either by doing contract
00:07:23.600 uh and then you do symbol equals like
00:07:26.160 Tesla, and then you do sec_type. Uh
00:07:29.440 sec_type can be like uh stock or option
00:07:34.040 or that sort of thing. I'll show you in
00:07:35.000 a second. Uh a um exchange, you have to
00:07:38.280 have an exchange and a currency. You
00:07:40.760 just have to have the minimum
00:07:42.360 information uh um
00:07:45.200 to uniquely identify the contract
00:07:47.200 because I'll show you in a second what
00:07:48.560 you do. Currency equals USD, and then
00:07:50.760 you do ib.qualifyContracts
00:07:53.240 a contract.
00:07:54.800 So, what this does is uh so, I guess I
00:07:57.400 messed up. Um Oh, uh sec_type is stock.
00:08:01.480 So, what this does, the
00:08:02.520 qualifyContracts, is it returns You can
00:08:05.040 put like many contracts. You can do like
00:08:06.840 contract contract
00:08:08.920 two, contract three. It'll turn a list
00:08:11.400 of all the valid contracts. And also, it
00:08:14.760 like mutates this contract object. So,
00:08:16.680 now as you see, if I write contract, you
00:08:19.040 see it added a conId and a primary
00:08:22.680 exchange, trading class, and that sort
00:08:24.800 of thing. And that's needed if like you
00:08:27.040 want to get like the options chain or
00:08:29.160 you want to do like combos and that sort
00:08:31.680 of thing. Um, that is that is uh needed
00:08:34.599 for that. Um, just a second. If you have
00:08:37.799 like um let's say you have like um
00:08:40.599 PyCharm or whatever, you can do control
00:08:42.440 B on contract, and you can see like
00:08:44.880 there's so many different types. There's
00:08:46.720 stock, option, future, index, uh uh
00:08:50.520 futures option, forex pair,
00:08:53.040 uh that sort of thing. Uh bag is a big
00:08:55.040 one we'll do. Uh um bag is basically a
00:08:58.520 uh combo contract. So, anyways, uh
00:09:01.840 there's These are also subclassed here.
00:09:04.680 Like option is subclassed subclassed
00:09:07.080 contract. Um, stock is subclassed. So,
00:09:10.200 we're usually not going to use the whole
00:09:12.320 the contract API, uh but I just want to
00:09:15.040 show you that it exists. Um, usually
00:09:17.440 what you're going to be doing actually
00:09:19.240 is going to do something like stock
00:09:20.800 equals stock.
00:09:22.760 Um
00:09:25.720 um symbol equals uh Tesla. Um, exchange
00:09:30.760 equals smart. Currency equals USD.
00:09:36.280 And then you And then you get stock. If
00:09:38.440 you just do stock, you don't have the
00:09:40.440 the um uh contract IDs and stuff. But
00:09:42.960 when you do ib.qualifyContracts
00:09:45.360 stock, you get the contract ID and
00:09:47.720 stuff. So, like you don't have to do it
00:09:50.240 sometimes, but like sometimes you're
00:09:51.760 going to need this. As you'll see in a
00:09:53.600 second. Okay. So, we We also get um
00:09:56.920 we can get more details on the contract
00:09:59.280 by doing ib.direct contract details. So,
00:10:02.440 let me just show you an example. I can
00:10:03.720 do like AMD AMD
00:10:06.720 equal stock
00:10:08.280 symbol equals
00:10:10.560 AMD.
00:10:12.320 And then I can do uh contract details
00:10:15.160 equals ib.direct
00:10:17.120 uh
00:10:18.320 contract details
00:10:20.240 AMD. I But But on purpose I did it like
00:10:23.320 this because um
00:10:25.240 uh it's going to show you like many
00:10:27.000 contracts. Like it's going to be
00:10:28.280 ambiguous. I didn't do exchange smart
00:10:31.040 currency equals US dollar. So, then you
00:10:33.200 can um
00:10:34.600 So, you can look at it like this
00:10:35.880 contract details like like this
00:10:38.720 which is kind of a mess. So, there's
00:10:40.520 like actually a helper function
00:10:42.960 uh where you can um
00:10:45.120 uh you can do um
00:10:47.200 there's one help helper function where
00:10:48.600 you can do like uh view it as a data
00:10:50.880 frame by doing util.df. You're going to
00:10:52.760 see me do this a lot. And you see you're
00:10:55.080 going to have contract, market name, min
00:10:56.920 tick, all this information. But if we
00:11:00.160 filter things out like um
00:11:02.720 let's say I call this uh
00:11:05.000 uh
00:11:06.280 let's say I call this df AMD contract
00:11:10.280 details
00:11:12.080 equals this and then I'll just print it
00:11:13.880 so you guys will have it.
00:11:15.800 If I filter out df AMD contract details
00:11:20.080 and I I want I I I only take the
00:11:23.040 contract with currency USD and exchange
00:11:25.080 equals smart, I only get one unique
00:11:27.160 contract. So, if I do like um
00:11:30.160 Okay, so like if I if I What What if I
00:11:32.480 can do something like this contract
00:11:34.800 and then I do two lists and then I do um
00:11:38.360 util
00:11:39.760 .df. I just look at the contracts.
00:11:43.240 Um and if I now
00:11:46.000 uh So, I'm just looking at the
00:11:46.960 contracts. And if I if I do now .query
00:11:51.280 uh currency equals USD and
00:11:55.920 uh exchange
00:11:57.600 And I don't know if you guys are
00:11:58.520 familiar with this. I should make a
00:12:00.200 Pandas tutorial. Um like a one one uh
00:12:04.360 Pandas thing a day.
00:12:06.120 Maybe I can do it as a short. I don't
00:12:07.800 know. If you guys like that idea, please
00:12:10.000 uh let me know. Ah. So, I spelled query
00:12:12.839 wrong. Okay. So, this is just gives you
00:12:15.280 like a unique uh
00:12:17.120 there's only one with exchange uh smart
00:12:20.080 currency equals USD. So, you can do a
00:12:22.160 forex example. You can do like uh euro
00:12:25.080 USD. You can do pair equals euro USD.
00:12:28.760 So, if I do uh euro USD, I get this
00:12:31.120 thing. And I can also do ib.direct
00:12:34.839 uh contract details
00:12:37.080 and you'll see it only has one because
00:12:38.680 it's actually unique. There's only one
00:12:40.280 euro USD.
00:12:42.000 Um so uh
00:12:48.200 Okay. So, me show you option contracts
00:12:51.080 because those are very fun for us
00:12:53.280 options uh
00:12:54.839 lovers. So, you can do call option
00:12:57.360 equals option
00:12:59.200 symbol equals whatever symbol. Let's say
00:13:01.680 I always use Tesla.
00:13:03.400 Um you you you do that. This is the
00:13:06.120 expiry, the last trade date or contract
00:13:08.839 month. You can do 2024. Let's What's
00:13:12.040 this Friday? 5:31.
00:13:14.600 Um you can do strike Oops. What did I
00:13:18.080 do?
00:13:19.240 Um strike equals 170. Exch-
00:13:23.440 Oops, sorry.
00:13:25.080 Strike equals 170.
00:13:32.640 Exchange
00:13:34.160 exchange equals smart.
00:13:38.200 Um currency
00:13:40.320 Uh
00:13:40.880 Sorry, guys.
00:13:42.680 Currency equals USD.
00:13:45.640 So, then I can do ib. Oh, I didn't do if
00:13:48.960 it's a call or put. So, I can do um
00:13:51.760 right
00:13:53.640 equals call.
00:13:55.240 So, now I can I can do ib.qualify
00:13:58.280 contracts to get the contract ID and
00:14:00.760 that sort of thing. Call option. Oh, so
00:14:03.280 You know what? I'll show you the
00:14:04.280 qualified contracts in a second. I want
00:14:05.760 to make a point about it. So, this is
00:14:08.360 the call option. So, the put option, we
00:14:10.680 can do the same thing except with um
00:14:13.400 right equals P. So, put option.
00:14:16.120 Okay. So, um
00:14:18.200 right equals P.
00:14:20.000 Okay. So, now you can do ib.qualify
00:14:23.800 contracts call option put option.
00:14:30.079 And then
00:14:31.320 uh now if I
00:14:32.720 it like mutates this object, so now I
00:14:34.600 can do call option and you see it gives
00:14:36.600 me the contract ID. So, um
00:14:39.880 what I wanted to say here is I wanted to
00:14:41.680 say like if you don't have like a combo
00:14:43.600 contract, you can actually access uh
00:14:47.079 um the contract with the con ID. So, I
00:14:50.480 don't I can actually do something like
00:14:51.959 this. I can do contract call option
00:14:55.200 .con ID
00:14:56.800 um con ID equals this. So, I I get this
00:15:07.079 I I call contract
00:15:09.640 equals like this. So, look at this. It
00:15:11.920 looks like this.
00:15:14.120 Call contract and then do call contract.
00:15:17.400 I get the call option as we expect. So,
00:15:20.880 the You can just use this unique
00:15:22.800 identifier.
00:15:24.360 Um maybe it'll uh be simpler for you
00:15:26.240 guys if
00:15:27.079 it make more sense if I just wrote this
00:15:28.520 number.
00:15:29.800 Uh
00:15:30.880 You know what? I'll show you for put
00:15:31.839 option and I'll actually write the
00:15:33.079 number. So, for put option, it'll be
00:15:35.160 like uh
00:15:36.880 um
00:15:37.839 put contract. Just in case I I I I said
00:15:40.320 it too fast
00:15:42.160 cuz uh
00:15:44.440 put option
00:15:46.320 uh put contract.
00:15:49.000 And then I'll call this put contract.
00:15:52.160 But then I'm going to I'm just going to
00:15:53.400 like specify I'm going to write that
00:15:54.959 actual uh contract ID just to show you
00:15:57.280 guys like uh
00:15:58.800 what I meant. Uh
00:16:00.839 I did uh .con ID. But in case you missed
00:16:04.160 it, you can just write the contract ID
00:16:05.839 like this.
00:16:07.480 Uh
00:16:08.320 uh equals uh
00:16:10.360 Is it an int or a string? I always
00:16:12.000 forget. Okay. So, that worked. Okay. So,
00:16:15.280 by the way, if you if you don't know
00:16:17.240 exactly what you want and you want to
00:16:18.720 search, you can do ib.rec matching
00:16:21.400 symbols. I think this works for bonds,
00:16:23.600 not just stocks. Uh but for stocks it
00:16:26.040 works for sure. So, you can do like uh
00:16:28.240 matches equals ib.rec
00:16:31.520 matching symbols
00:16:33.680 and let's try like Intel.
00:16:36.000 Intel.
00:16:38.280 And then
00:16:39.400 uh match contracts.
00:16:41.480 Matches looks like this.
00:16:43.839 Uh so, it's kind of a mess. There's all
00:16:45.200 these contract descriptions.
00:16:47.079 So, we can do something like um
00:16:50.440 uh match contracts that match contracts
00:16:53.440 equals cuz there's way more information
00:16:55.480 as description like uh technology, that
00:16:58.560 sort of thing. So, match contracts, we
00:17:01.360 can do um
00:17:03.079 uh something like uh m.contract
00:17:06.599 for m in
00:17:08.720 uh matches.
00:17:11.439 Uh and then we can do util.df matches.
00:17:15.240 Match uh
00:17:17.640 contracts.
00:17:19.760 Okay. So, now you see like these are all
00:17:21.640 the matching contracts.
00:17:23.880 Uh Intel
00:17:25.520 uh If you if you then like do a que-
00:17:28.600 query
00:17:30.560 uh exchange equals smart.
00:17:35.440 And then uh uh
00:17:37.920 Something's wrong. Anyways, uh
00:17:42.320 Anyways, uh
00:17:44.160 I don't want to get into too much detail
00:17:45.440 cuz I never use this. I just wanted to
00:17:47.480 mention it. So, if you want to search,
00:17:49.840 you can do like rec matching symbols. I
00:17:52.520 actually found this most useful when I
00:17:54.880 was trying to do bond stuff, but I don't
00:17:57.480 trade bonds. But anyways,
00:17:59.880 um
00:18:00.960 Okay. So, like okay, but a lot of you
00:18:03.000 guys are interested in option chains,
00:18:04.720 right? So, option chains is actually um
00:18:07.520 where you do need the .con ID thing. So,
00:18:10.800 um
00:18:11.400 there's a function called a
00:18:12.640 reqSecDefParams
00:18:14.679 and that's how you can get options
00:18:16.440 chains. So, I can do like um
00:18:18.800 chains
00:18:20.600 chains equals ib.rec
00:18:23.520 sec
00:18:24.800 defParams. And then you put underlying
00:18:27.760 symbol
00:18:29.040 equals uh stock.
00:18:31.400 um
00:18:32.640 symbol.
00:18:33.880 Oops.
00:18:36.360 Uh and then we do There's a weird thing
00:18:38.240 foot fop exchange. You just leave that
00:18:40.720 empty. I don't know why they even have
00:18:43.240 it, but they tell you to leave it empty.
00:18:45.440 Underlying
00:18:46.800 uh um
00:18:47.880 sec type.
00:18:49.480 Oh, and I forgot to mention if you want
00:18:51.280 documentation, you can do
00:18:53.200 tws-api.documentation
00:18:56.200 and you get this documentation. It'll
00:18:58.280 tell you this is obsolete.
00:19:00.720 Uh and then you get here. This will give
00:19:02.360 you the Trader Workstation documentation
00:19:04.720 and it's kind of one-to-one between this
00:19:06.720 and the IB in sync uh IB sync. It's
00:19:09.600 literally the same thing. So, like um it
00:19:12.400 just it's literally the same thing. You
00:19:14.080 guys will figure it out. But that's just
00:19:15.919 like a small side note. Okay. So, chains
00:19:18.720 and then I do underlying uh sec
00:19:21.919 uh security type equals uh Oops.
00:19:25.240 Uh
00:19:26.080 stock.sec
00:19:28.280 uh type. And then what else do I need? I
00:19:30.800 need uh Let's see what else is there.
00:19:33.440 Un-
00:19:35.080 Underlying con ID equals stock. This is
00:19:38.040 where I need the con ID. That's why we
00:19:39.600 needed to do the ib.
00:19:41.800 uh qualify contracts cuz we needed this
00:19:43.480 extra info. Okay. So, this gives you a
00:19:45.520 bunch of information.
00:19:47.760 Um but let's filter it out exchange
00:19:50.440 equals smart because there's only one
00:19:52.760 such thing. So, I'll do like chain
00:19:55.200 equals chain for chain in chains if
00:20:00.200 chain
00:20:02.120 .exchange
00:20:05.120 equals
00:20:06.440 smart.
00:20:08.800 Does that work? Oh.
00:20:13.520 Okay. So, just to show you length chain
00:20:16.280 is one.
00:20:17.880 We'll take the first one.
00:20:20.640 Chain. Okay. So, now we can look at um
00:20:24.120 the data frame of chain. So, chain looks
00:20:26.120 like this.
00:20:27.360 So, if I were to do um and this is also
00:20:29.840 another Pandas thing, util.df chain
00:20:34.520 I get um
00:20:36.320 Oops, that does not look good. Uh oh,
00:20:38.360 cuz I need it as a list. Sorry. So, I
00:20:40.520 actually it was better to keep it like
00:20:41.880 this. Um
00:20:43.920 Uh util.df chain
00:20:47.280 Okay. So, I I have it like this. I have
00:20:49.800 the exchange, underlying conId, ID,
00:20:52.600 trading class, multiplier, expirations,
00:20:55.200 and strikes. But, we want to see it in
00:20:57.160 like a nice format. So, you can actually
00:20:59.640 use this explode function.
00:21:01.760 And again, if you guys are interested in
00:21:04.320 Pandas videos, I'm willing to do one a
00:21:07.560 day like a short or something.
00:21:10.200 Um so, explode expirations gives you
00:21:12.680 expirations and that explode
00:21:15.200 uh strikes gives you the strikes. Not
00:21:17.960 all these combos will be valid, by the
00:21:19.600 way. Um
00:21:21.040 And you know what? Uh
00:21:22.960 it is sorted, but let's do um
00:21:25.840 So, yeah, that's how you can see the
00:21:27.280 option chain. So, maybe I'll call it df
00:21:29.880 chain.
00:21:31.400 And then I'll do uh df chain.
00:21:34.760 Okay. So, that's the options chain. You
00:21:37.000 see you have the um
00:21:38.560 expirations and you have the strikes.
00:21:40.600 Okay. So, uh just an example, if you
00:21:43.440 want like uh to get only the valid
00:21:45.360 contracts, we can do like we can have
00:21:47.480 like a minimum strike and a maximum
00:21:49.840 strike.
00:21:50.840 So, we can do like uh and we can do
00:21:53.080 ib.qualifyContracts
00:21:55.200 to find um only the ones that are valid.
00:21:58.280 So, I'll show you just real quickly how
00:21:59.640 to do that. So, let's say we want like
00:22:02.120 um
00:22:02.679 options between let's just say between
00:22:04.679 these two dates.
00:22:07.040 And then we'll have like a min strike
00:22:09.640 equals let's say we Tesla's about 178
00:22:13.160 177 or something. So, we want strikes
00:22:15.720 between 160 and max strike we'll do like
00:22:18.040 180.
00:22:21.160 And then I'll I'll I'll set like this
00:22:22.960 contracts object.
00:22:25.040 And then I'm going to iterate through um
00:22:28.120 the uh
00:22:29.560 uh
00:22:30.400 chain thing uh the expirations on it.
00:22:34.160 And I'm going to um
00:22:36.160 uh I'm going to get all the contracts.
00:22:38.760 And you'll see that some of them are not
00:22:40.240 valid. But, when I do
00:22:41.800 ib.qualifyContracts,
00:22:43.400 they become valid. So, like okay. So, um
00:22:46.240 and I'm talking a bit fast because uh
00:22:48.679 um this is going to be a long video
00:22:50.200 otherwise. Uh how long I've already been
00:22:52.800 23 minutes. Okay. So, um
00:22:56.200 So, uh
00:22:57.640 and because I actually, you know what?
00:22:59.320 Let me actually do it like this.
00:23:01.560 So, um
00:23:03.080 it'll make everything work. I'll I'll
00:23:04.840 set chain still to that. And then I'll
00:23:07.040 do chain like this. And now this will
00:23:09.800 work. So, I'm going through the original
00:23:11.640 chain. I'm going through the expirations
00:23:14.120 and the strikes, and I'm making sure
00:23:16.000 it's between min and max strike, and I'm
00:23:18.120 appending it to the contracts. So, I get
00:23:19.800 a list of these contracts. So, like I
00:23:22.400 have um
00:23:24.040 I'm kind of rushing through this.
00:23:26.160 Contracts.
00:23:27.600 Uh oops, max strike.
00:23:30.920 So, I have
00:23:32.120 uh
00:23:33.560 contracts.
00:23:35.360 So, I have 120 contracts. And how do
00:23:37.400 they look? They look like uh let's say
00:23:39.640 contracts
00:23:41.200 zero. It's
00:23:42.920 what you expect, right? But, some of
00:23:44.960 these will not be valid. So, I can do
00:23:46.840 like valid contracts equals
00:23:51.160 ib.qualifyContracts
00:23:53.800 contracts.
00:23:55.240 And then it'll go through and uh
00:23:57.960 Oh, because uh it's a list, you have to
00:24:01.440 I actually have
00:24:02.600 You don't put it as a list, you have to
00:24:04.000 put it as like
00:24:05.440 um
00:24:06.640 arguments. So, you have to do this
00:24:08.160 thing, I think.
00:24:09.560 So, valid See, it's going to get rid of
00:24:11.760 a lot of things that are not valid. So,
00:24:15.280 this basically gives you like the valid
00:24:17.040 option chain.
00:24:18.400 So, once this thing is eventually done
00:24:23.200 get a valid option chain.
00:24:25.760 Okay.
00:24:49.240 Um So, valid contracts. So, now I do
00:24:52.320 length of that.
00:24:53.840 Valid contracts length contracts. Just
00:24:56.320 to show you guys
00:24:57.920 uh So, like 88 of them were valid. Some
00:25:00.840 of them were not valid. Okay. So, uh now
00:25:04.040 you have valid contracts if you want to
00:25:06.200 use that. Okay. You can create combos,
00:25:09.520 uh but you know what? Um
00:25:11.400 I think uh combos are uh beyond the
00:25:13.560 scope of this video.
00:25:15.520 Um But, I will refer you to my other
00:25:18.080 videos on combos. Uh So, um So, like
00:25:22.320 okay. So, let me just refer you to some
00:25:24.280 past videos. So, I have a video here
00:25:26.840 about options. I have a video here and
00:25:30.320 similarly about options and Greeks and
00:25:33.400 volatility smile. But, if you're really
00:25:35.360 interested in combos um there is a few
00:25:38.520 combos. There's uh This one is a combo
00:25:42.040 example, a bull call debit spread. And
00:25:45.520 uh this one is another uh combo example,
00:25:48.679 combo trades. And I do have another
00:25:51.080 video for combos. By the way, uh my
00:25:53.520 channel is
00:25:55.160 uh YouTube.
00:26:00.160 Um
00:26:05.800 My channel uh So, what do I have in my
00:26:07.679 channel? I have uh
00:26:09.600 combo.
00:26:12.400 Uh I I think I might have another combo
00:26:14.480 video.
00:26:16.000 Uh combo trade um
00:26:20.960 Uh I have another video uh I guess on
00:26:23.200 this. Uh
00:26:25.440 Okay.
00:26:32.640 So, let me actually just give you guys a
00:26:35.080 link to this video.
00:26:37.160 Okay. So, I have three uh combo videos
00:26:40.000 that should give uh enough examples, I I
00:26:42.600 would say. Um
00:26:44.120 So, uh let's do this other video. Uh
00:26:47.760 And uh if you want more on combos, uh
00:26:50.120 let me know. I just think it's a little
00:26:51.480 bit overblown to talk about it in this
00:26:53.840 video, especially cuz like the time
00:26:56.440 constraints. Um
00:26:59.840 So, another combo video is here, combo
00:27:03.080 and combo and combo. Okay. This is combo
00:27:05.800 contracts mean like bull call spreads or
00:27:07.760 like let's say ratio spreads or calendar
00:27:10.280 spreads. You have five calls, two puts,
00:27:12.920 all that stuff. Um okay. So, now um
00:27:16.600 And sorry, it just this video will never
00:27:18.160 end if we talk about everything. So, now
00:27:20.440 let Okay, let's talk about like uh how
00:27:22.480 you can view your positions. So, you can
00:27:24.160 view your positions by doing
00:27:25.920 ib.positions.
00:27:27.920 Uh you can also do ib.portfolio. It
00:27:29.840 gives you a little bit more information.
00:27:32.480 But, I ib.positions is better. It gives
00:27:35.200 you like the unrealized and realized
00:27:37.440 P&amp;L, but I found those to be not so
00:27:39.440 accurate. So, I prefer just using the
00:27:42.040 positions thing.
00:27:43.720 Um Okay. And uh
00:27:46.400 again, similar to the other thing, you
00:27:48.400 can use util.df to view it in a nice
00:27:50.880 way.
00:27:51.880 Position ib.positions.
00:27:54.640 Positions.
00:27:57.120 So, now you can see I have an option and
00:27:59.240 a stock, and I have average cost and
00:28:01.360 that sort of thing.
00:28:02.880 Uh I I recommend these things you
00:28:05.240 calculate yourself, like the average
00:28:06.960 cost and stuff, because their accounting
00:28:09.360 is not always perfect uh
00:28:11.800 the way you expect with if you specified
00:28:14.560 uh first in, first out, last in, last
00:28:16.480 out, that sort of thing. So, I can do df
00:28:18.520 positions equals like this.
00:28:21.040 I can do df positions, but like this is
00:28:23.440 kind of ugly. So, maybe you want to like
00:28:26.080 uh parse it in a nice way. So, one way
00:28:28.080 you can do that is you can like Let's
00:28:29.960 extract the symbol. So, we can do df uh
00:28:33.280 positions.contract.apply
00:28:37.120 lambda L
00:28:39.640 L.symbol. That it gives you the symbol.
00:28:42.760 And you know I'll print it every time,
00:28:44.360 df positions. So, that gives me the
00:28:46.360 symbol. But, like we want to know like
00:28:49.320 uh what contract what security type it
00:28:51.360 is, right? So, positions I'll do
00:28:53.600 secType.
00:28:55.760 Or uh equals df positions.contract
00:28:59.840 that apply lambda L
00:29:02.919 L.secType, I think it's called.
00:29:06.360 So, now I see option and I see stock.
00:29:09.280 But, we also for options we probably
00:29:11.320 want like
00:29:12.640 to know if it's a call or a put. So, we
00:29:14.600 can do df positions.right
00:29:17.600 equals df positions.contract
00:29:21.679 that apply lambda
00:29:24.760 L L.right. You can actually do this in
00:29:27.520 one line, but let's not do that like
00:29:29.679 that. df position Oh. Oh, sorry. Uh it's
00:29:33.600 it's uh call or put or um
00:29:37.240 if L.secType
00:29:40.159 equals opt.
00:29:41.880 Um And just to remind you guys, like the
00:29:44.800 option, remember I showed you the
00:29:47.440 contract? See Oh, sorry. Contract and
00:29:51.120 then you have option here.
00:29:53.640 And option is sub classes contract with
00:29:59.440 and you'll see it like it has like um
00:30:02.480 it has like a sec type of opt. Where is
00:30:06.080 that?
00:30:07.360 Oh, sorry here. Sec type of opt. So like
00:30:11.520 it's very useful to like jump in the
00:30:13.400 code. So like right if it's otherwise
00:30:17.760 let's say
00:30:18.960 none or something. So let's you know
00:30:21.560 let's see if this worked actually.
00:30:23.800 Uh
00:30:25.320 L.write if L.that's sec type equals opt.
00:30:29.440 Uh so you see right equals call
00:30:32.000 otherwise none.
00:30:34.360 Uh okay and then let's just add the
00:30:36.320 strike and expiration. So I'll do DF
00:30:38.960 positions uh expiration
00:30:43.400 uh strike and similar to these thing
00:30:46.440 these guys. So like basically like like
00:30:48.840 this one
00:30:50.080 except I'll take out the strike and
00:30:52.520 expiration. Okay, so I'll do like um
00:30:56.360 I'll do L.
00:30:57.600 um
00:30:59.120 last trade date or contract
00:31:03.480 month
00:31:04.880 and L.
00:31:06.480 uh
00:31:08.120 strike. Let's see if this worked. This
00:31:10.720 is just a easier way to see it. I guess
00:31:12.640 I spelled something wrong.
00:31:14.280 I always last trade date or contract
00:31:16.920 month.
00:31:18.440 Okay, so this is just a easier way to
00:31:20.560 see it. If you have an option you have
00:31:22.280 like option call strike expiration.
00:31:25.280 Anyways, so just I want to make a big
00:31:27.520 note. So this is a asynchronous
00:31:30.880 system and it constantly updates the
00:31:33.080 current
00:31:34.640 state of everything.
00:31:36.720 So um
00:31:38.680 what's important is
00:31:40.840 so everything is constantly updated
00:31:42.520 assuming you have a connection and all
00:31:43.960 that good stuff. And then when your
00:31:46.200 connection
00:31:47.520 restored it keeps it updated. But like
00:31:50.000 you can also set a request to make sure
00:31:52.080 you're at the current state. Um but it
00:31:54.520 takes a lot more time just to make sure
00:31:56.960 you're synchronized and it's blocking.
00:31:59.120 This IB.positions
00:32:01.600 I mean
00:32:02.880 you can you can do it in a non-blocking
00:32:04.880 way. So you can do IB.req positions. Um
00:32:08.560 I don't want to get too much into this
00:32:10.320 but you can do requests
00:32:12.520 similar to like other things but
00:32:14.760 requests are blocking and they take a
00:32:16.679 lot more time but IB.positions
00:32:18.960 constantly updates automatically when
00:32:20.960 there are changes in the system. Okay,
00:32:23.640 so you can view account information also
00:32:26.679 by doing like IB.
00:32:29.360 account summary.
00:32:31.320 And there's also a thing called
00:32:32.880 IB.account values but account summary as
00:32:35.480 you see you have like tag account value
00:32:38.960 cushion all that all this information.
00:32:42.280 Um and again we can view it nicer in a
00:32:44.600 data as a data frame by doing like
00:32:47.560 DF account
00:32:49.560 summary equals we always use this
00:32:51.480 util.DF IB.account summary.
00:32:55.480 Um okay, so we can do this.
00:32:59.920 Uh DF account summary like this and you
00:33:03.520 see you have account
00:33:05.720 and you know what you have account
00:33:08.080 account type uh cushion all that stuff.
00:33:11.960 Um
00:33:14.040 You you can also um
00:33:17.600 Uh you can you can search like
00:33:20.280 how much my account is worth net
00:33:22.280 liquidation and certainty you can do DF
00:33:24.040 account summary DF account
00:33:26.040 summary.tag.string.contains
00:33:30.120 let's say net
00:33:31.800 liquidation
00:33:33.920 case equals false.
00:33:36.160 Um and and that then I can see oh oops
00:33:39.840 net not new.
00:33:41.920 So
00:33:43.640 net lick
00:33:45.320 quidation.
00:33:47.640 So this is how much the account is
00:33:48.880 worth. The account is worth almost a
00:33:50.880 million dollars cuz it's not a real
00:33:52.240 account. Okay. Anyways, that's that's
00:33:55.440 something else.
00:33:57.040 There's also an IB.account values that
00:33:59.080 has like kind of similar things. Uh but
00:34:01.760 not exactly the same so you should check
00:34:03.520 that. But if you actually also like each
00:34:06.520 of them has like account value um as
00:34:09.719 their thing but it's not the same. This
00:34:12.320 they don't have the same things.
00:34:14.719 They have slightly different things.
00:34:16.159 There is some overlap. There are
00:34:17.399 slightly different things. Um again you
00:34:20.199 can also do this like uh
00:34:22.440 uh util.DF thing to make to view it
00:34:25.560 nicer.
00:34:26.879 Um you can also
00:34:29.359 do uh
00:34:33.040 You can see your account values like
00:34:35.199 this. The tags there's many tags. You
00:34:37.840 can do DF account values that tag
00:34:42.879 that to list that'll be the tag values
00:34:45.440 you have. Like accrued cash next day
00:34:49.040 trade remaining. So all this margin
00:34:50.960 information and like option values and
00:34:53.960 realized P&amp;Ls and stuff like that. So if
00:34:56.719 you're interested it has all that stuff.
00:34:59.320 Let's not spend too much time on this
00:35:01.480 cuz it's already 35 minutes. Okay, so
00:35:04.280 let me now talk about one of the most
00:35:06.880 important things if not the most
00:35:08.400 important thing is and that is ordering.
00:35:11.160 Order and I wrote this warning basically
00:35:13.240 don't run this cuz this will make real
00:35:15.320 orders.
00:35:16.400 And if you do somehow convince yourself
00:35:18.920 to run it make sure you first run on a
00:35:20.600 demo account. I will say there's some
00:35:22.600 hiccups with demo accounts like some
00:35:24.920 orders don't get filled stay on pending
00:35:27.040 submit. Um
00:35:29.760 for example like combo orders for me. So
00:35:32.320 some demo accounts are not perfect or
00:35:34.240 paper accounts I mean. But be very
00:35:36.760 careful with this. There's millions of
00:35:39.000 order types. There's millions of
00:35:40.480 conditions. There's good to to cancel.
00:35:43.560 There's time conditions. There's
00:35:45.400 conditions on other prices if Tesla
00:35:48.400 buy Tesla only if Nvidia is under a
00:35:50.440 thousand.
00:35:51.720 There's market on close margin
00:35:53.440 conditions time conditions only buy
00:35:56.040 between 3:00 and 4:00 p.m. Um and the
00:35:59.359 big order things are like sub class like
00:36:02.359 limit order market order stop order stop
00:36:04.800 limit order. Those are sub class but
00:36:06.760 there's millions of maybe not millions
00:36:08.720 but there's a lot of order types.
00:36:10.680 And there are also bracket and child
00:36:12.840 orders and stuff like that and I do have
00:36:14.680 a lot of other videos on that. We're not
00:36:16.880 going to cover that exactly here but
00:36:18.760 just note that exist. And let me just
00:36:20.359 show you for a second again when we go
00:36:22.120 into the code
00:36:23.600 we see like I do control B on order. You
00:36:26.640 can see you have a million different
00:36:28.400 types of things you can do. There's like
00:36:29.680 delta neutral orders all this weird
00:36:31.920 stuff. But like the big ones like limit
00:36:34.400 order and market order stop order are
00:36:36.600 sub classed. So as you see like limit
00:36:39.040 order is basically your order with order
00:36:41.200 type is LMT action equals action total
00:36:44.359 quantity limit price. So like it's sub
00:36:47.320 classed to make it easier for you. Okay,
00:36:49.480 so let me show you placing order. So you
00:36:52.600 need the order and you need the
00:36:54.600 contract.
00:36:56.680 And the output of the order is as a
00:36:59.120 trade object and I'll show you that in a
00:37:00.560 second. So let's say I can do something
00:37:02.720 like order equals order.
00:37:06.040 I'm going to do it without the sub
00:37:08.320 classed limit order thing just to show
00:37:10.200 you guys for a second. Total quantity
00:37:11.960 equals one limit price equals 170
00:37:16.800 order type
00:37:19.800 order type equals limit cuz I'm going to
00:37:22.320 do it like the
00:37:24.320 hard way. Action equals buy. So this is
00:37:27.320 the order. So now I can do trade equals
00:37:30.240 IB.place order contract
00:37:34.000 you need a contract and order.
00:37:36.000 So that's the trade object. And what
00:37:37.760 does a trade object have? It has a few
00:37:40.880 things. It has the order itself.
00:37:43.080 Oh,
00:37:44.320 you know what let's let's run this let's
00:37:46.480 run this twice.
00:37:47.880 This is a new order now. I just want to
00:37:49.600 show you something. Cuz that order is
00:37:51.480 order ID equals uh
00:37:54.920 it has order ID equals zero and now you
00:37:56.640 do trade and then you can look at the
00:37:58.440 trades order. It gives it an order ID.
00:38:01.000 So I do that order. See it gave it an
00:38:02.800 order ID. And this is like the unique
00:38:05.960 identifier ID identifier thing but for
00:38:09.040 algo trading we're only focused on this
00:38:10.960 order ID thing. So trade.order ID
00:38:14.600 uh as you see it like it it first it had
00:38:17.080 nothing but when you placed the order it
00:38:18.920 gave it like the next available one
00:38:20.600 which is this. You also have trade
00:38:23.520 you have sorry you have trade
00:38:26.040 trade.order status.
00:38:28.359 And order status is submitted.
00:38:31.560 Um okay and then you have trade.fills.
00:38:35.640 This is if it was fills you can see what
00:38:37.320 was filled or what was not filled.
00:38:39.040 Nothing was filled yet. Trade.log is the
00:38:41.520 log of the status of the order. So when
00:38:43.840 you first placed the order it's at
00:38:45.680 pending submit and then it gets to
00:38:47.560 pre-submitted and then submitted. And
00:38:49.240 then when it gets filled it gets to
00:38:50.640 filled. Or canceled it gets like pending
00:38:53.280 cancel and cancel. There's many
00:38:55.280 different
00:38:56.359 there's a lot of permutations but always
00:38:58.240 pending submit and then pre-submit and
00:39:01.040 submitted.
00:39:02.560 That's always.
00:39:04.200 So that's you can have the log and
00:39:05.920 there's also like a error thing I never
00:39:07.760 really use it but anyways just so you
00:39:10.040 guys know. Okay, so um
00:39:13.480 uh so okay. Let's say you want to modify
00:39:16.440 the order right? And if this order is
00:39:19.880 still
00:39:21.800 active so I can do if I look at
00:39:24.040 trade.order
00:39:25.840 that
00:39:27.640 orders
00:39:28.920 status
00:39:30.680 that
00:39:32.240 I see it's submitted. I think there's
00:39:33.960 also a trade that order that is
00:39:37.040 is active or something. Is active?
00:39:40.480 I forgot off the top of my head. Um
00:39:43.920 order uh
00:39:46.080 status that is that status
00:39:50.560 is done. I don't know. I forgot.
00:39:53.800 But uh
00:39:55.240 this is all this is from uh Anyway, so
00:39:58.320 if it's not filled, you can change the
00:40:00.400 order. How do you change the order?
00:40:02.600 Uh you have to modify the the It's by
00:40:05.920 order ID you have to modify it. So, I
00:40:07.400 have to take the order part. So, I I
00:40:09.480 take this order part. And and now I can
00:40:12.600 change the limit price. So, previously
00:40:14.280 the limit price was 170. I can now do
00:40:16.800 limit price. As long as it's not filled
00:40:18.800 yet, I can set it to 160.
00:40:21.280 Uh
00:40:21.880 all right? And then I I just do trade
00:40:24.840 equals ib.
00:40:26.720 that place order
00:40:28.400 um contract
00:40:30.040 Oops.
00:40:31.200 contract order
00:40:33.760 So, now you see trade.order.
00:40:37.520 You see I have uh Now it's a 160.
00:40:41.680 Um and let's look at the log. You see
00:40:44.600 the log had submitted message modify
00:40:48.040 message modified modified modified.
00:40:51.120 Okay, so that makes sense. Okay. So, uh
00:40:54.320 this is the modifying order. Okay.
00:40:57.000 Uh it didn't fill. Um Okay, let me just
00:40:59.720 show you guys a market order for a
00:41:01.640 second uh because you can use the
00:41:04.040 Nothing is filled yet. I'll I'll get to
00:41:05.640 that in a second. But like um
00:41:08.200 Okay.
00:41:10.480 You know what? Let's show you the
00:41:11.480 canceling orders first, okay? And maybe
00:41:13.800 I should actually have put it up here.
00:41:15.960 So, I'll do like this. Um
00:41:18.720 Uh
00:41:19.840 canceling orders.
00:41:23.320 Okay, so for canceling orders you you
00:41:25.160 can you can do ib.cancel
00:41:28.920 order and you just do the order. So,
00:41:31.240 there's a helper there's like a thing
00:41:33.120 ib.open_orders.
00:41:35.040 So, you can see the orders that are
00:41:36.160 open. And uh as and once you place the
00:41:39.160 order, it'll change that. There's also
00:41:41.160 ib.open_trades, by the way. And that
00:41:43.920 just gives you the whole trade info.
00:41:46.160 It's similar to ib.open_orders. But to
00:41:48.200 cancel the orders,
00:41:50.000 you can do for
00:41:51.800 order in ib.open_orders,
00:41:54.680 ib.cancel.
00:41:58.360 So, order.
00:42:00.760 You know what? Let me show you ahead of
00:42:01.880 time. I can do like uh ib.open_orders
00:42:05.880 like this.
00:42:07.280 Uh ib.cancel_order
00:42:09.720 or order. And then I can do
00:42:11.680 ib.open_orders.
00:42:13.800 You know it might still have it because
00:42:15.560 it still has it because it's uh it takes
00:42:18.000 time to cancel. So, now So, it's this is
00:42:20.640 more like it. Okay. So, anyways, uh cuz
00:42:23.440 it doesn't right away It's asynchronous,
00:42:25.200 right? So, like it doesn't wait for this
00:42:27.440 to cancel before it goes to here. So,
00:42:29.440 that's why when I put it under it didn't
00:42:31.120 cancel it yet. Okay. So, like I said,
00:42:33.440 there's subclasses of popular orders.
00:42:35.680 So, market order you can do like buy
00:42:38.520 100. Um so, I can do like um
00:42:42.480 So, let let me show you I can do like
00:42:43.960 market order.
00:42:47.520 Order equals like this.
00:42:49.880 And then I can do ib.place_order
00:42:52.920 uh contract Oops.
00:42:56.720 act
00:42:58.200 market order
00:43:01.080 And then it placed the order.
00:43:03.320 Um
00:43:04.120 Uh but you notice I have this order
00:43:06.520 still open.
00:43:07.920 Uh market order should fill right away.
00:43:10.040 But we because we are um
00:43:12.400 pre-market post-market after hours,
00:43:15.560 that's why there's no such thing as
00:43:17.040 market hours after hours. So, let's
00:43:18.680 actually
00:43:19.920 uh go ahead and cancel that.
00:43:22.440 Okay, so um that's the market order. So,
00:43:25.480 there's also stop orders.
00:43:27.800 Uh you could do stop order.
00:43:31.120 Uh
00:43:32.920 buy uh So, let me I'll be precise. So,
00:43:35.440 like
00:43:36.400 uh
00:43:38.000 uh
00:43:40.160 You know what? Okay, let's uh actually
00:43:41.840 write the limit order first.
00:43:43.960 You know why? Because
00:43:45.560 uh
00:43:46.440 Yeah, you know what? Let's do the stop
00:43:47.760 order first. But uh stop order the stop
00:43:50.960 price is called aux is called it's
00:43:53.200 called stop price.
00:43:55.000 But like be careful. It's called stop
00:43:57.120 price in stop order thing. But when you
00:43:59.720 actually look at the subclass
00:44:02.200 uh for or uh stop order, I'll do like
00:44:05.760 stop order
00:44:07.840 control B. You see that um
00:44:10.880 uh when it's implementing the stop
00:44:12.880 order,
00:44:14.040 you see order
00:44:15.720 uh type is uh stop. And aux price is the
00:44:19.200 stop price. So, aux price
00:44:21.480 in the big picture in the order is is
00:44:23.680 stop price. So, like let me show you
00:44:25.480 stop order in two ways, actually. So, I
00:44:28.040 can do stop order.
00:44:29.960 I can do a stop price is 100. And
00:44:33.280 uh and actually that would um
00:44:37.160 Uh
00:44:37.960 let's say stop Let's do something above
00:44:39.840 200. And then I can do another way of
00:44:42.120 doing it is like writing the actual
00:44:43.840 order.
00:44:45.160 Cuz I just want to make clear on the
00:44:46.560 parameter. It's called aux it's called
00:44:48.560 aux price.
00:44:50.400 aux price
00:44:52.120 And then it's uh order type.
00:44:56.080 Order type equals uh stop.
00:44:59.359 Um I think that's it. Uh oh, there's
00:45:02.320 also a total quantity.
00:45:04.880 Uh sometimes you you need to write in
00:45:06.760 the right order
00:45:08.000 equals 100. Um
00:45:11.640 total
00:45:13.359 All right. So, these are equivalent ways
00:45:14.960 of doing it.
00:45:16.280 Um
00:45:17.359 uh
00:45:19.080 Uh duplicate order ID is my favorite. Uh
00:45:21.600 let's cancel all these orders.
00:45:24.000 Okay, so now I can do stop order like
00:45:26.000 this. Oh, cuz I wrote market order.
00:45:29.200 stop order
00:45:30.640 Okay, and then this is the same. All
00:45:32.800 right. Um
00:45:36.320 This is equivalent.
00:45:39.560 Note that um
00:45:41.800 um aux
00:45:43.880 price is stop price.
00:45:47.600 Um so,
00:45:49.480 uh
00:45:50.840 I'll write stop order.
00:45:53.480 Uh
00:46:01.800 Uh positional argument uh follows uh
00:46:07.920 Oh, cuz I have this this equal. Okay.
00:46:11.280 Okay, so uh yeah. Oh, okay. So, I wrote
00:46:13.560 here. You can look at open orders.
00:46:16.160 Uh you can look at um
00:46:19.080 uh trades ib.open_trades.
00:46:24.040 Um
00:46:26.720 You can look at your fills. So far, we
00:46:28.680 have no fills. Oh, we have fills cuz I
00:46:31.160 played with this before the video. But
00:46:33.640 uh you can look at the um open orders
00:46:36.640 uh
00:46:37.240 uh and then I'll write um
00:46:39.400 open trades. You can do um it's just the
00:46:42.480 orders with more info. ib.open_trades.
00:46:46.480 And then you can look at ib.trades
00:46:49.120 in general.
00:46:50.760 Uh and then you have uh
00:46:54.640 ib ib.orders in general.
00:46:57.840 So, orders and trades actually give you
00:47:00.320 more than more of the clients. But the
00:47:02.480 open ones only give you the current
00:47:05.200 client unless it's a master client. So,
00:47:07.800 we can also look at fills by doing
00:47:09.280 ib.fills.
00:47:10.960 Okay, so we actually have uh two fills.
00:47:13.200 Let me actually show you guys. So, I
00:47:15.400 have um
00:47:18.120 length ib.fills
00:47:20.800 equals two. But note like no matter what
00:47:23.280 we do, none of the things we did now got
00:47:25.720 filled.
00:47:26.880 Um so, let's cancel all the orders,
00:47:28.600 actually.
00:47:29.800 So, uh let's cancel all the orders.
00:47:32.720 So, why didn't it get filled? It's
00:47:34.200 because uh we are um
00:47:36.960 outside regular trading hours. So, uh
00:47:39.400 let's try to get it to be filled.
00:47:41.800 Okay, so let's write a limit order.
00:47:46.880 Um
00:47:50.440 I don't know why I uh
00:47:54.120 Okay, so let's write limit order
00:47:57.080 outside regular trading hours equals
00:48:02.400 Um limit order. This is like the
00:48:04.600 subclass I was telling you about.
00:48:06.680 Action equals buy.
00:48:09.600 Uh total quantity equals 100.
00:48:12.680 Limit price equals 180 outside regular
00:48:16.560 uh
00:48:17.840 side
00:48:20.240 RTH equals true.
00:48:23.920 This is the important thing. So, like um
00:48:27.240 So,
00:48:28.280 uh
00:48:30.960 uh
00:48:32.880 What did I do wrong? I I must have done
00:48:35.000 something wrong.
00:48:38.320 Um Okay, so price I said buy at 180, so
00:48:41.080 it should fill.
00:48:42.720 What did I do? Oh, outside regular
00:48:44.440 trading hours.
00:48:45.960 Regular trading hours.
00:48:49.040 Uh
00:48:53.120 Limit order outside
00:49:02.520 Uh
00:49:04.880 I have some weird margin issues. This is
00:49:07.560 like a a weird thing with the demo
00:49:09.440 account. If I do ib.positions,
00:49:12.240 let me maybe uh get rid of my positions.
00:49:14.720 So, uh I have
00:49:16.720 Oh, and I have a weird thing in my demo
00:49:18.240 account that I can't really sell uh
00:49:21.280 um
00:49:22.440 after hours. Okay, but let's if we buy
00:49:24.480 let's buy one share. Okay, so buying one
00:49:27.400 share worked, right? So, now if we look
00:49:29.840 at um
00:49:31.240 the positions, remember we saw we had um
00:49:35.120 we had uh
00:49:36.600 uh
00:49:37.280 stock Tesla position 320. Now we should
00:49:40.280 see 320.
00:49:44.560 That's weird. Um
00:49:47.160 What's the status?
00:49:49.400 Sometimes demo accounts do weird stuff.
00:49:51.400 Order status, that status. Why is it
00:49:53.920 submitted?
00:49:55.480 Is it What's the price of Tesla? It
00:49:56.880 should be filled cuz I did buy one.
00:50:00.720 It's weird. Um
00:50:05.120 Uh let's try sell for a second cuz
00:50:08.120 sometimes in a demo account it only lets
00:50:09.960 me do one of the things. So let's say I
00:50:11.840 want to do sell and I'll do 170.
00:50:14.840 And let's do Let's see if this worked.
00:50:17.600 Uh
00:50:19.840 Oh, I know what's the problem.
00:50:23.000 So contract
00:50:25.480 for some reason is a option. We want
00:50:28.800 Let's do it for the stock we had. Sorry
00:50:30.640 about that. Stock. So now I do Now I see
00:50:34.560 the order status as you filled. Yeah. So
00:50:37.360 now I see I get this
00:50:39.880 added one.
00:50:41.640 Sorry. That's what 321. I don't know how
00:50:44.720 this
00:50:45.680 became contract became
00:50:47.760 option all of a sudden. But 321,
00:50:50.920 see it worked. And then let's just do
00:50:52.520 another one for like 100.
00:50:55.160 And then you'll see I'll be 331.
00:50:57.880 421, sorry. And order status filled. And
00:51:01.080 then we can do length ib.fills.
00:51:04.120 We'll get like four.
00:51:06.240 Okay.
00:51:07.400 Great.
00:51:09.400 Okay. So I wanted to say place order is
00:51:11.600 not blocking and it will not wait to
00:51:14.280 what what happens with the order. So you
00:51:15.960 can do place order and even if it's a
00:51:17.880 market order, like something else can
00:51:19.600 happen in the meantime. It's not block.
00:51:22.040 I mean, it's not blocking.
00:51:24.720 So like if you want to make sure it's
00:51:26.920 blocking
00:51:28.320 like
00:51:30.160 your rest of your code
00:51:32.720 you don't want anything in your code to
00:51:34.200 happen until it happens. You can do like
00:51:36.960 Oh, and this is the This is the done
00:51:39.160 thing I was looking for. You can do like
00:51:42.840 while trade is not done
00:51:46.000 uh
00:51:47.720 like that. And then you do
00:51:49.680 ib.waitOnUpdate and then it'll finish.
00:51:52.520 And then let me actually I'm printing
00:51:53.880 the order status every time.
00:51:57.720 Oh, it's cuz I have this stupid
00:51:59.280 contract. Sorry, guys.
00:52:01.200 It's same thing every time. Uh
00:52:04.760 Okay. Um
00:52:07.200 I don't know how I made contract the
00:52:08.800 option. But see like it it like while
00:52:12.040 trade not done, this makes it blocking.
00:52:14.400 Pending submit, pending submit,
00:52:15.720 pre-submitted and then it'll it filled
00:52:17.480 at the end. I don't have it here, but if
00:52:19.800 you do trade that order status, you'll
00:52:21.400 see it's filled.
00:52:23.000 Okay. So I said let's look at the fills
00:52:26.000 again, but you guys believe me.
00:52:28.120 Okay. Sorry. I'm just rushing because
00:52:30.440 it's already 52 minutes.
00:52:33.040 Okay. So like some I have many videos on
00:52:37.480 some more advanced concepts like on
00:52:39.640 orders. Like I have trailing stop
00:52:41.920 orders.
00:52:43.120 I have bracket orders and like with
00:52:45.160 parent and child orders and that sort of
00:52:47.000 thing. I have one cancels all order. Say
00:52:49.640 like you want to like make either this
00:52:51.640 order or that order and if one triggers,
00:52:53.640 you cancel the other one.
00:52:55.520 So I have that. I have conditional
00:52:57.000 orders. So it's like buy Nvidia only if
00:52:59.640 AMD is under 200, something like that.
00:53:02.880 So that's
00:53:04.640 those videos you can check out. I
00:53:06.120 probably have a few more videos on that,
00:53:08.800 but those are some of the ones that are
00:53:11.160 at the top of my head. It's in my
00:53:12.560 GitHub. Anyways, um
00:53:15.400 Okay. So now let's talk about market
00:53:18.400 data, finally. The good stuff. Okay. So
00:53:21.400 market data
00:53:23.240 is not free. You need a few
00:53:24.640 subscriptions. You only really need two
00:53:26.400 subscriptions. The US equity and options
00:53:29.520 add-on streaming bundle and the US
00:53:32.120 security snapshot and futures bundle.
00:53:35.080 Um and a subscription is per user. I
00:53:37.760 recommend you have two users cuz like if
00:53:40.600 you then like
00:53:42.200 use the the market data and then you
00:53:44.160 check on your phone and it'll disconnect
00:53:45.760 your market data and it'll screw things
00:53:47.600 up and it'll be really annoying. So
00:53:49.360 actually Oh wow, you haven't seen me the
00:53:51.160 whole time on video. Sorry.
00:53:54.880 My camera fell. Okay. So I recommend you
00:53:58.040 have two users and I'll make another
00:53:59.840 video on that if you guys need. But
00:54:02.280 let's try to get the
00:54:04.359 um
00:54:05.800 Let's try to get the
00:54:07.600 Let me show you guys the subscriptions
00:54:09.320 you need. So for this you need to
00:54:11.320 actually go to um
00:54:13.520 Let's see you can Google IB
00:54:17.280 client portal.
00:54:19.520 And then you go to the client portal.
00:54:22.400 You log in or did I log in?
00:54:28.520 Okay. Let me log in without showing you
00:54:31.600 guys my credentials for a second.
00:54:47.320 Oh, sorry.
00:55:05.000 Okay, you log in to the
00:55:07.359 to this account.
00:55:09.680 So now you go to settings.
00:55:13.160 Um
00:55:23.680 In settings you see
00:55:25.720 you have
00:55:26.880 uh
00:55:28.320 uh market data subscriptions.
00:55:33.440 This account is kind of out of
00:55:34.760 commission soon. So like you need these
00:55:37.480 two ones. You need the US and equity
00:55:40.120 add-on option stream and you need this
00:55:42.640 US security snapshot and futures
00:55:45.760 value bundle. There's also a few other
00:55:48.000 ones that are useful, but these two are
00:55:49.840 the minimum you need. 14 and a half
00:55:51.920 bucks. If you spend over 30, I guess
00:55:53.840 they wave the $10. So four and a half
00:55:56.160 bucks if you trade a lot. Um 14 and a
00:55:59.280 half if you don't. But you need those
00:56:00.800 two things. Okay. So that said, let's
00:56:04.080 talk a bit about market data.
00:56:07.440 I guess the next video will will talk
00:56:09.280 about this a lot more, but like the
00:56:11.359 first thing you guys want to probably
00:56:13.320 interested in is getting like historical
00:56:15.120 bars or getting bar data in general,
00:56:17.359 right? So
00:56:19.840 So we're we'll start with that. Um So
00:56:23.160 like to get historical bars, you do this
00:56:25.520 thing. You do like
00:56:27.160 uh bars equals ib.req
00:56:30.480 historical
00:56:32.160 data.
00:56:33.720 And then you do the contract. Let's do
00:56:35.840 contract equals stock, Tesla of course.
00:56:39.200 End date time. Okay, so end date time
00:56:41.080 can be a like a Python date time.
00:56:43.520 But
00:56:45.160 why is it Oh, oops. req I wrote req his
00:56:49.080 histogram data. You need req
00:56:52.880 req
00:56:53.920 uh
00:56:55.240 historical data.
00:56:57.520 It's crazy how like my camera was messed
00:56:59.520 up the whole video.
00:57:01.000 But uh hopefully hopefully I mean it's
00:57:03.000 better not to see me, right? So
00:57:06.280 a contract equals stock end date time
00:57:09.440 equals
00:57:11.120 This is until the current time, but you
00:57:12.720 can have a date time. Uh duration string
00:57:15.800 is like how many days.
00:57:17.640 For small bars, you can't put that much.
00:57:19.640 You'll have to do a loop over this
00:57:20.920 thing. And I have other videos that show
00:57:23.000 that. Bar size settings. This is if you
00:57:24.920 want like five-minute bars.
00:57:27.080 And what to show. You could do trades.
00:57:29.840 You can do
00:57:31.400 bid bid ask midpoint. Again, if you do
00:57:34.680 tws API historical
00:57:38.320 data, you'll see like you'll have like
00:57:42.480 things that will show you like what to
00:57:43.720 show things. It'll say like um
00:57:47.440 historical bar data.
00:57:49.640 And you'll see like what to show. You
00:57:51.840 can have uh
00:57:53.359 uh trades, midpoint, bid ask, bid ask.
00:57:57.320 Adjust So read these. We're going to use
00:58:00.000 trades cuz it's the simplest one. And
00:58:02.200 then let's do two more things cuz we're
00:58:03.880 after hours. Uh let's do use regular
00:58:07.240 trading hours equals false and let's use
00:58:10.160 keep up to date equals true because this
00:58:11.920 keeps it up to date and I'll show you in
00:58:13.400 a second. So now you get bars and bars
00:58:16.800 is just a list like this. A list of
00:58:19.400 bars, but the last bar keeps getting
00:58:21.240 updated. So you can use the nice
00:58:24.600 tool to do to view it. You can do
00:58:27.640 util.dfbars.
00:58:29.440 And look look at the last one. Notice
00:58:31.280 the volume at 2863
00:58:34.200 and bar counts of four.
00:58:36.080 So now I I I I update it.
00:58:40.040 I guess this is after hours, so it
00:58:41.600 doesn't update that much, but
00:58:44.480 uh
00:58:48.320 Did I do keep up
00:58:49.960 keep up to date equals true? Okay,
00:58:51.880 sorry.
00:58:54.400 Uh
00:58:56.840 Yeah, so
00:58:58.160 during the market hours this would
00:58:59.720 update every 5 seconds, but because
00:59:02.880 there isn't
00:59:04.440 that much data,
00:59:06.359 it's taking a bit of time.
00:59:08.320 Because this is after hours, it's not
00:59:09.720 pre-market. So it's like very slow.
00:59:12.960 Um Okay. Let's
00:59:15.560 Let's chill on this for a second and
00:59:17.640 then let's do another thing. So you can
00:59:20.040 also do
00:59:21.200 real-time bars. And by the way,
00:59:24.880 yeah, see now a bar count is five, so it
00:59:26.920 did update it. And let's just keep this
00:59:29.440 thing in mind for a second. Length of
00:59:31.040 bars is 544.
00:59:32.960 Right? So, util.df
00:59:35.680 bars
00:59:36.880 is five and let's see it it keeps
00:59:38.880 updating it. You'll see in a second.
00:59:41.200 This
00:59:42.360 like this interval cuz we're at 517,
00:59:45.360 this interval is not done yet. So, it
00:59:47.640 keeps updating this interval
00:59:50.320 and when it there's a new interval,
00:59:52.280 it'll give you the new interval with
00:59:54.080 volume minus equals minus one. And when
00:59:57.120 the pre when you just finished an
00:59:59.040 interval, but that just we'll talk about
01:00:01.200 that a lot more in the next video about
01:00:03.120 trading. See, bar count is nine, so it's
01:00:05.160 updating.
01:00:06.400 It's still 544 because we are um
01:00:09.800 uh not done with the interval. But okay,
01:00:13.080 so this is nice cuz you can keep
01:00:15.040 updating it and when there's a new bar,
01:00:17.280 there's like a I'll show you in the next
01:00:19.480 video, there's like a has new bar is
01:00:21.520 true, so you can like do things only on
01:00:23.640 full bars if you don't want to do it on
01:00:25.560 partial bars, but um the issue with this
01:00:29.760 thing I'll show you in a second is
01:00:32.360 if your uh uh data um if your data gets
01:00:36.680 disconnected,
01:00:38.280 um you
01:00:40.080 um
01:00:40.840 it you get screwed. So, let me just show
01:00:42.400 you an example. So, um
01:00:45.920 so uh I think you guys get my point that
01:00:48.520 like it keeps updating itself, right?
01:00:51.360 Um but like okay, let's say I do
01:00:53.840 bars
01:00:55.120 5 second, right? And I do uh
01:00:58.040 duration string one day, bar size
01:01:00.360 setting is 5 seconds.
01:01:02.520 What to show is trades, so bars 5
01:01:04.720 seconds, right?
01:01:10.800 Keep up to date is true.
01:01:17.360 So, I do length bars 5 seconds is 9588.
01:01:21.720 And then it it should whenever there's
01:01:23.520 an update, it should automatically
01:01:25.120 update it. Okay.
01:01:27.720 Um because it's
01:01:29.480 after hours when there's no activity in
01:01:31.800 a 5-second period, it like waits until
01:01:33.600 there's a new activity. It'll backfill
01:01:35.880 all there is. See, I added three bars.
01:01:38.280 See, it's 9591. It keeps updating 9592.
01:01:41.480 Okay. But now
01:01:43.600 the the the problem with this, I'll show
01:01:45.520 you what the problem with this is is
01:01:48.120 um this is perfect. So easy. You have
01:01:51.480 the historical and you have the live
01:01:53.120 update. You can do all your algorithms
01:01:55.200 you want. But the problem is it's not
01:01:57.360 robust to internet disconnections. So,
01:02:00.720 let me show you what is that those are
01:02:03.440 real-time bars. So, like real-time bars
01:02:06.720 are like this, live bars, and they're
01:02:08.920 always 5 seconds. I don't even know why
01:02:11.080 they have a parameter of like bar size
01:02:14.000 because it's always 5 seconds no matter
01:02:15.600 what you put, but req real-time bars uh
01:02:20.040 stock contract equals stock. Let's do
01:02:24.200 the rest. Bar size, it's always five
01:02:26.840 even if you put more.
01:02:28.520 But what to show is trades. There's a
01:02:30.240 little less options here. Again, you
01:02:32.200 look at the documentation for that. And
01:02:34.320 then use regular trading hours is false.
01:02:36.840 So, now
01:02:38.400 live bars is very similar except it just
01:02:42.480 it's it's it's like real-time bar. It's
01:02:44.840 very similar except it does not have the
01:02:46.440 historical part. But there's a huge
01:02:48.400 difference. So, let watch this. I do
01:02:50.400 length Okay, so watch this.
01:02:53.040 Um
01:02:54.280 Okay, so um
01:02:56.600 so watch this. I'll do uh
01:02:58.560 bef uh
01:02:59.960 bef before
01:03:03.080 internet disconnect,
01:03:06.960 what do we have? We have uh length of
01:03:10.000 live bars
01:03:11.760 and length of bars 5 seconds.
01:03:15.400 Uh 89610,
01:03:17.240 right?
01:03:18.400 And then we can click it and you see
01:03:19.800 99611. Okay. So, now right after
01:03:25.480 after
01:03:26.800 internet
01:03:29.200 disconnect,
01:03:31.400 so now I'm going to purposely disconnect
01:03:33.600 my internet.
01:03:35.280 Um
01:03:43.720 disconnect.
01:03:55.920 Uh it's very robust.
01:03:58.080 Is this still connected somehow? How do
01:03:59.760 you disconnect?
01:04:02.160 Disconnect. Okay.
01:04:04.560 So, now it's stuck, right?
01:04:08.760 This this is seriously automatically try
01:04:10.640 to disconnect. Okay.
01:04:13.920 Okay.
01:04:17.760 You You notice You notice the numbers,
01:04:20.240 right?
01:04:22.560 Okay.
01:04:25.560 Okay, I get this disconnect error,
01:04:27.640 right? So, now I reconnect to my
01:04:29.840 internet.
01:04:34.160 And then you get and then you run this.
01:04:37.080 Uh
01:04:42.920 Uh am I connected?
01:04:46.280 Okay, sorry.
01:04:50.000 See, look at the difference. After
01:04:53.800 After internet disconnect, only live
01:04:56.520 bars um
01:04:58.400 gets fixed.
01:05:00.400 Historical
01:05:01.960 cool bars with updates does not. That is
01:05:05.400 the difference. So, I recommend for
01:05:07.240 beginners just use historical bars, but
01:05:09.880 when you get advanced,
01:05:11.800 do the
01:05:12.920 historical bars and then update with the
01:05:15.120 with the live bars, the real-time bars.
01:05:17.400 And I have video about how to update
01:05:19.120 that. Um so, we'll I'll link that in a
01:05:22.200 second. Uh okay, so now you probably
01:05:25.200 want market data like real-time
01:05:28.280 data like uh
01:05:30.480 you probably want like uh
01:05:33.280 more granular data than 5 seconds like
01:05:35.960 snapshots, that sort of thing. So, you
01:05:37.960 can actually do that. You can do ticker
01:05:39.600 equals ib.req
01:05:41.600 market data and then your contract
01:05:44.000 equals stock
01:05:46.560 symbol generic tick list equals There's
01:05:50.200 a lot of options. Again, look at the
01:05:51.600 documentation. Snapshot
01:05:54.280 uh equals true means you only get one
01:05:56.800 snapshot. And regulatory snapshot equals
01:05:59.400 false. It This is if you want true, it's
01:06:02.400 the national best bid offer thing and it
01:06:05.720 costs a little bit of money
01:06:07.560 and you get like the real best thing,
01:06:09.640 but like it's
01:06:11.480 for practical purposes, it's the same.
01:06:13.840 Uh so, now you I do ib.sleep two.
01:06:17.280 This is just cuz the ticker doesn't get
01:06:18.800 filled right away and it's asynchronous.
01:06:20.880 So, it'll give me nan if I don't. So, I
01:06:23.440 do ticker. I can do ticker.bid,
01:06:26.200 ticker.ask,
01:06:27.800 and ticker
01:06:29.320 ticker.midpoint, for example.
01:06:32.280 And then I can also have a lot of other
01:06:34.040 things. Um
01:06:35.680 My other videos will show it. So, I
01:06:37.280 guess uh
01:06:38.400 Tesla really dipped after hours, I
01:06:41.640 guess.
01:06:42.720 Um nothing uh It closed at 176.75, so
01:06:47.280 yeah, it did dip quite a bit. I don't
01:06:49.240 wonder what happened.
01:06:50.680 It's Tesla, so anything's possible,
01:06:52.800 unfortunately.
01:06:54.640 Um okay.
01:06:56.840 So, um
01:06:58.520 if somehow you like do request market
01:07:00.880 data for a lot of tickers and you lose
01:07:02.359 track of the ticker, you can also do
01:07:04.480 this. You can do ib.ticker
01:07:06.840 of your contract of your contract object
01:07:09.840 and you can get the uh
01:07:11.720 the ticker.
01:07:12.960 You can also cancel the market data
01:07:14.680 subscription by doing
01:07:16.640 ib
01:07:19.200 uh ib.cancel
01:07:22.080 market data
01:07:23.720 and then you write your contract.
01:07:25.000 Contract equals stock.
01:07:29.160 And then I'll just write this as
01:07:30.680 contract equals this to make it clear.
01:07:34.720 And you can get Okay, so this gives you
01:07:36.880 a snapshot. Like it means it refreshes
01:07:38.880 it like every second.
01:07:40.560 But what if you want real tick by tick
01:07:43.320 data? You want every damn tick.
01:07:45.440 So, like there's a few many different
01:07:47.320 options.
01:07:48.920 So, let's just say tws API tick by tick
01:07:53.720 data just to show you guys. So, there's
01:07:56.080 like tick by tick data and there's all
01:07:57.920 these options. You can do last, all
01:08:00.240 last, bid ask, and midpoint. And there's
01:08:02.880 differences between them. It's not the
01:08:04.840 point of this video. I just want to show
01:08:07.320 you that it it has. But you can only do
01:08:09.520 three at a time. That's disadvantage.
01:08:12.400 You can buy more, but the three at a
01:08:14.359 time is a disadvantage for many. But
01:08:16.520 like to get tick by tick data, you do
01:08:18.759 ticker equals ib.req
01:08:23.040 uh
01:08:24.359 tick by tick data contract equals
01:08:27.279 contract um
01:08:29.160 tick
01:08:30.160 type equals let's do all last.
01:08:33.160 And number of ticks
01:08:35.719 equals zero. What is this number of
01:08:36.920 ticks thing again?
01:08:38.640 Um
01:08:58.799 Uh I don't remember uh this thing. Uh
01:09:01.880 I used to know this stuff, but anyways,
01:09:03.839 you do ticker like this. Uh
01:09:06.920 Uh
01:09:07.520 Oh, cuz my contract is an option, sorry.
01:09:10.880 Uh so, let's do stock. You can do for
01:09:13.479 options, I think. Uh
01:09:15.600 it just the
01:09:17.560 market is closed, but
01:09:19.479 so ticker like this and you can get the
01:09:21.560 ticks by doing ticker.tick by ticks.
01:09:25.160 Um
01:09:26.279 Eventually, it'll
01:09:27.960 it'll give you like some ticks.
01:09:31.279 You do need some sort of call back to
01:09:34.279 like
01:09:35.359 keep track of this stuff if you want to
01:09:37.720 save everything.
01:09:39.200 Okay, and you can cancel the tick by
01:09:40.799 tick data also like this.
01:09:42.920 Oh, contract equals stock now.
01:09:46.120 I don't know where I got that mixed up.
01:09:48.200 Okay, so anyways this is a bit of a long
01:09:50.439 video so I want to like
01:09:52.720 want to go strong in the next video
01:09:55.480 like we'll do real strategies and that
01:09:57.120 sort of thing especially if I get enough
01:09:59.600 people to like and subscribe enjoy to
01:10:03.040 show that it actually helped them. But
01:10:04.880 there is some additional information in
01:10:06.440 my older videos like I have like
01:10:09.120 updating historical bars with real time
01:10:11.240 updates. This is to handle the
01:10:13.080 robustness issue if your internet
01:10:14.800 connection drops. I have a video on
01:10:17.160 historical tick data. Oh, I guess I
01:10:19.320 didn't show you here but like you can
01:10:21.080 get historical tick data. It's a little
01:10:23.360 annoying because it rounds the nearest
01:10:25.160 second and we know ticks are are like
01:10:27.720 fractions of a second.
01:10:30.160 And then I have a few videos on tick by
01:10:31.960 tick data why is Tesla crashing?
01:10:35.120 I have a few videos on getting
01:10:36.360 historical bar data for a lot of
01:10:39.040 history. I think you can get up to 3
01:10:41.040 years.
01:10:43.040 So those are what these videos are on.
01:10:45.840 And I have
01:10:47.720 I have more videos on getting 5 second
01:10:49.560 bar data,
01:10:51.640 getting crypto data,
01:10:54.040 Greeks and implied volatility. And we
01:10:56.800 covered only a certain amount of things
01:10:58.600 there's so many things in this IB and
01:11:00.360 sync slash IBA sync package there's so
01:11:03.040 many different things we didn't touch.
01:11:05.480 One more quick thing there's logging
01:11:07.840 so you can do logging equals debug and
01:11:09.680 it'll kind of show you everything. So if
01:11:11.600 I go like ib.fills it shows me like
01:11:14.400 It shows me like it'll show you like
01:11:15.800 every little thing you do.
01:11:17.600 So um
01:11:21.080 So if I do like ib.placeOrder
01:11:23.480 uh
01:11:25.040 um
01:11:26.680 stock
01:11:28.360 limit order buy 100
01:11:32.080 150 see the the debug gives you like all
01:11:35.840 this stuff.
01:11:37.800 So let's actually put it here to show
01:11:39.640 you guys.
01:11:41.320 Look at how much how much info it gives
01:11:43.600 you when you do logging
01:11:46.200 it to log the console debug.
01:11:48.440 Okay, and you can disconnect by doing
01:11:50.440 ib.
01:11:52.400 disconnect.
01:11:54.320 Okay. So now I
01:11:57.240 I kind of wanted to talk to you a little
01:11:58.960 bit about the um master client ID just
01:12:02.520 for a second. So if I do remember we
01:12:06.160 which which
01:12:07.880 client did we use here?
01:12:09.880 We used um
01:12:13.920 We used client zero. So client zero is
01:12:16.600 special cuz you can see your phone
01:12:18.520 orders with client zero. Which is cool
01:12:21.960 but
01:12:23.960 it's a special you it's the only one you
01:12:26.400 can see client orders. Okay, so I
01:12:28.080 actually like
01:12:29.680 um you can only see client uh um
01:12:34.720 um phone orders with client ID equals
01:12:39.000 zero.
01:12:40.120 Okay, that's one thing. Okay, so it's a
01:12:42.920 special one.
01:12:44.320 But
01:12:46.040 but um
01:12:47.840 master client ID sees
01:12:51.360 all clients
01:12:53.800 except phone unless
01:12:57.000 it is also client ID zero.
01:13:02.480 So I'll write it as two notes.
01:13:04.800 So you can only see phone orders with
01:13:08.240 client ID zero and then master client ID
01:13:10.800 sees all client orders
01:13:13.280 except for phone orders unless it's also
01:13:15.840 client ID zero. So let me show you an
01:13:17.200 example. So let's call this IB0 equals
01:13:20.640 IB um and then IB0. That connect client
01:13:26.160 ID equals zero.
01:13:27.800 So if I do okay, I can do IB0
01:13:31.640 that open orders.
01:13:34.360 I get these open orders, right? But what
01:13:36.800 if I do
01:13:38.360 um
01:13:39.160 So remember my
01:13:41.040 master ID was uh
01:13:44.240 API I do settings.
01:13:47.480 Master was three.
01:13:49.400 So what if I do
01:13:51.040 um
01:13:51.800 two, right? I do like four for example
01:13:55.480 client ID four.
01:13:58.680 And then I do
01:14:00.400 see the debug thing shows me every
01:14:02.080 little thing. It's a little annoying
01:14:03.800 sometimes.
01:14:05.040 So you see
01:14:07.320 I don't see any of the orders. But if I
01:14:10.440 were to do two three because three is my
01:14:13.680 uh
01:14:14.360 master
01:14:17.680 but master sees everything.
01:14:22.600 So if I do this I do um
01:14:25.440 oops
01:14:26.680 It's a little annoying the debug thing
01:14:28.680 uh
01:14:30.360 I should have removed it. Open orders.
01:14:34.920 So
01:14:36.680 you see the open orders. Anyways
01:14:39.040 I hope you guys enjoyed the this video
01:14:42.000 um
01:14:45.960 I'll just write uh
01:14:50.080 client ID equals four so
01:14:53.680 not master and doesn't
01:14:57.760 see other client
01:15:00.760 ID orders. Anyways, I hope you guys
01:15:03.480 enjoyed this video. I'm sorry the camera
01:15:05.520 was a little messed up. The code will be
01:15:07.360 on GitHub. Please like and subscribe if
01:15:09.480 you're new and thank you so much.
01:15:11.880 Hopefully the next video will be done. I
01:15:13.880 have a lot of personal stuff going on
01:15:15.360 but
01:15:16.880 if I get a lot of support I'll try to do
01:15:18.800 it sooner.

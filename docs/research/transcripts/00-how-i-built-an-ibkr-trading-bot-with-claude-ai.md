
# tactiq.io free youtube transcript

# How I Built an Interactive Brokers Trading Bot with Claude AI (IBKR API Tutorial)

# https://www.youtube.com/watch/wHB8XLNhAw0

00:00:01.080 Good day everybody. Brian here
00:00:02.840 coinlabsnet.com.
00:00:06.000 I'm going to be talking about the uh
00:00:09.280 good old new app that I've got developed
00:00:12.280 here.
00:00:13.280 I'm going to go over it, go over some of
00:00:15.440 the funding strategies that you may
00:00:17.120 struggle with when it comes to futures
00:00:18.720 option and futures like
00:00:20.360 and options for Interactive Brokers. And
00:00:23.720 uh
00:00:24.960 yeah, so uh
00:00:28.080 what
00:00:29.320 This is probably one of the longest apps
00:00:31.000 I've worked with using AI.
00:00:34.200 I lost week. Uh it's pretty close to
00:00:36.160 getting to its point where it's pretty
00:00:37.880 well
00:00:38.920 complete. And I want to show you uh
00:00:42.560 the demo of it what it can do. Now,
00:00:44.440 first thing is I won't be releasing it
00:00:46.120 to this anybody, but I want to showcase
00:00:48.120 this to people so that they can see what
00:00:50.280 they can do and develop with AI and
00:00:53.720 Interactive Brokers. But again, you need
00:00:55.400 to have something sophisticated like
00:00:57.960 I developed everything here with uh
00:00:59.520 Claude code in the VS
00:01:02.080 code extension.
00:01:03.600 So, that's what I did. I used it with a
00:01:05.160 code and it cost me a couple hundred
00:01:06.720 bucks to get working and develop. But I
00:01:08.920 just want to show it to you. So,
00:01:11.920 uh here it is um
00:01:14.280 in its full glory.
00:01:16.040 In here we have um server
00:01:19.880 that's running uh in the background
00:01:22.400 here. So, this is it there.
00:01:24.400 You can see
00:01:26.200 um
00:01:28.160 at the bottom here in the window
00:01:31.280 that I don't have Interactive Brokers
00:01:33.080 TWS set up.
00:01:35.080 So, I'm going to
00:01:36.600 fire that up. Now, I'm not going to load
00:01:39.200 up all my data so people can see it
00:01:41.160 obviously.
00:01:42.640 But uh I just want to show you
00:01:44.920 what uh how this works. So,
00:01:47.480 essentially what this app will do is
00:01:49.080 it's going to go through the full
00:01:50.600 functioning
00:01:52.120 working
00:01:53.840 apps or
00:01:55.280 strategy bots that I've got working.
00:01:57.960 There's only two.
00:01:59.280 The gold that I've mentioned and also uh
00:02:02.760 uh a um Bitcoin Ethereum or Ethereum
00:02:05.840 Bitcoin
00:02:07.080 spread uh once I can get that working.
00:02:09.038 So, let me just log in here. Now,
00:02:10.919 initially I tried to
00:02:12.959 do all of this in paper trading. It is
00:02:15.200 not going to work. You have to be fully
00:02:18.560 uh
00:02:19.680 subscribed
00:02:21.080 to uh uh market data if you're going to
00:02:23.560 use Interactive Brokers.
00:02:25.760 You also I'll I'll show you what I've
00:02:27.880 I've I've just
00:02:29.600 um did some interesting things here. So,
00:02:33.800 I'm just going through all my
00:02:34.680 verification. I haven't used the support
00:02:37.640 in uh
00:02:39.080 Interactive Brokers for a long time here
00:02:41.600 uh about 2 years. I've been focused more
00:02:43.880 on the
00:02:45.040 operations of um
00:02:47.840 of uh
00:02:50.720 Okay, so we're loading in TWS as we
00:02:53.680 speak.
00:02:54.920 That's on my other screen. So, right
00:02:56.760 now,
00:02:57.760 as you see here, this is pretty well the
00:02:59.600 whole
00:03:00.880 functionality of this app. I've put in
00:03:03.239 there a simulation uh so that you can
00:03:06.280 see
00:03:07.560 that um simulation is if you're
00:03:12.080 off hours on weekends, you can use this.
00:03:14.360 It's obviously
00:03:16.120 not going to be anywhere close to the
00:03:17.600 real world. Um
00:03:20.720 I'm still waiting for uh
00:03:23.000 this TWS to to load in. Also, we've got
00:03:27.440 uh
00:03:28.080 the uh bot connection here. This is very
00:03:30.360 important here. I'm going to show you
00:03:31.480 what this does. Once we get logged in.
00:03:34.200 Here we can test the TWS connection. We
00:03:37.080 can list contracts and show available
00:03:40.120 uh expirations and test market data.
00:03:42.320 Just depends, really. We also have here
00:03:44.880 two uh functions
00:03:46.920 uh to test uh buying and selling, in
00:03:49.760 this case, an ES contract.
00:03:52.560 Um and then in here you can see that we
00:03:55.200 have the capabilities to test
00:03:57.720 connection.
00:03:59.000 Um and also we can put in a to test with
00:04:03.680 particular a contract our exchange
00:04:08.120 and all that fun stuff as well.
00:04:12.400 So,
00:04:13.640 um
00:04:14.800 we are now logged in. So, I do know
00:04:18.279 we are logged in. So, if I test connect
00:04:20.880 you can see here testing connection.
00:04:23.280 It should turn green.
00:04:27.120 Let it turn green.
00:04:29.320 There it is. Okay. So, we're going to
00:04:32.120 test this out on ES
00:04:34.600 is the P 400. Show available
00:04:37.600 expirations
00:04:40.320 as well.
00:04:43.120 And that's very slow. I just talked to
00:04:45.120 the IBKR Interactive Brokers support.
00:04:48.640 They did say everything's slow right
00:04:49.919 now. So, you can see here it did load in
00:04:52.240 two expiration for ES. Now, this is real
00:04:54.640 market data. So, when you you load up
00:04:56.960 your TWS, I'm not paper trading anymore.
00:04:59.320 I am
00:05:00.480 actually
00:05:01.960 uh
00:05:02.520 trading uh in real data, meaning real
00:05:05.400 the real account. And
00:05:07.240 there's a couple things I want you to be
00:05:08.360 aware of.
00:05:09.680 Um
00:05:10.640 so that you know exactly
00:05:13.680 what we're dealing with here. So,
00:05:16.000 um hopefully you're a member of my uh
00:05:18.040 group uh forum.
00:05:20.160 If not, I'll show you where to go. I've
00:05:21.800 now opened it up so anybody can
00:05:24.480 uh go through that.
00:05:26.280 So, so you're on the Quant Labs net
00:05:29.440 uh dot com website.
00:05:31.520 Um we've got a bunch of options here
00:05:33.960 once it loads up.
00:05:37.600 Okay, there it is. You can just go into
00:05:38.960 more, okay? And then go into groups,
00:05:41.800 okay? And in there there's one group
00:05:44.320 that's open to everybody that everyone
00:05:46.160 can see. I just opened it up uh earlier
00:05:48.080 this week. Just go in here, Quant Labs
00:05:50.840 uh public. That's what you're looking
00:05:52.400 for. This one right here.
00:05:54.360 And if you want to comment, post, you
00:05:56.240 have to register. But anyone anyone can
00:05:58.360 view this.
00:05:59.640 So, these are the sort of things I've
00:06:00.840 just posted that you need to be aware of
00:06:02.640 before
00:06:03.720 anything uh when you when you start
00:06:05.880 trading options and futures.
00:06:08.680 Okay.
00:06:09.680 So, first things first,
00:06:12.520 um
00:06:13.560 here's the first comment.
00:06:16.280 Uh one right here.
00:06:18.960 Okay.
00:06:20.040 So, in order to subscribe to futures and
00:06:22.160 options, these are the instructions,
00:06:24.400 okay? To get that working, okay?
00:06:27.800 The there but there's some initial
00:06:29.200 requirements here.
00:06:31.200 So,
00:06:32.480 if you want to do futures and options,
00:06:36.280 uh you will need uh to have at least I
00:06:40.400 think they said $2,500
00:06:42.880 in your account, US dollars equivalent.
00:06:45.640 Okay? And in there I've got the
00:06:47.080 instructions how to set the um
00:06:50.520 futures trading up, okay? It's all
00:06:52.919 there.
00:06:54.120 Um and then like I said, you need to
00:06:56.720 have permission in the futures.
00:06:58.840 Make sure your account's a margin type,
00:07:00.560 not a cash
00:07:01.919 account. Um you have 2,500 US in there.
00:07:05.680 Also,
00:07:07.160 depending on what you want to trade. In
00:07:08.400 my case, I'm going to be trading
00:07:10.919 uh these
00:07:12.480 right here.
00:07:14.480 So, these are the namely are uh posts
00:07:16.520 here.
00:07:17.880 Uh if you want to
00:07:20.480 uh get access. But the these margin
00:07:22.240 requirements change day by day. So, this
00:07:23.880 could radically sh-
00:07:25.600 uh change.
00:07:27.120 So, here we have uh just four that I'm
00:07:29.440 initially starting with.
00:07:31.200 Again, I mentioned this as well, the
00:07:33.080 micro gold.
00:07:34.760 This is the amount you need for total
00:07:36.240 margin. This is from Grok.
00:07:38.919 Uh DX, again that's on the ICE. So,
00:07:43.400 MGC and MBT, these are micro Bitcoin.
00:07:47.120 Uh these are available on these two, MGC
00:07:51.400 and MB MET, are available on uh
00:07:56.520 on uh CME.
00:07:58.440 And then you have the DX, which is a
00:08:00.400 dollar index as well. If I should start
00:08:02.160 to figure out a
00:08:03.640 strategy for that to trade uh as well.
00:08:05.800 That's on ICE
00:08:07.560 as well. So, these are all the require
00:08:09.440 margin requirements funded in your
00:08:11.920 account to make just one contract, one
00:08:15.400 uh fulfill one contract. Okay. So, we we
00:08:18.960 need to
00:08:20.240 be aware of that.
00:08:21.800 Okay. So, let's come back to our app
00:08:23.840 now.
00:08:24.880 Okay. So, theoretically, we should be
00:08:27.080 able to buy just the ES
00:08:29.480 or a uh buy an one ES or a sell one ES.
00:08:34.679 Here, it won't work because I don't have
00:08:36.719 the proper funding. Boo hoo hoo. My
00:08:38.760 account I got to set up
00:08:40.559 for that. But, we can test that. I've
00:08:43.080 got all the messages in the console I
00:08:44.800 just showed you
00:08:46.160 earlier in the uh
00:08:48.600 in the uh server thing.
00:08:51.280 This right here. Okay. So, those
00:08:53.120 messages will pop up.
00:08:55.320 Okay. So, now we have the ES. I've shown
00:08:57.960 you the connectivities working.
00:09:00.440 All right. So,
00:09:02.240 here's what I have set up so far. Uh
00:09:04.480 I've talked about this in my streams
00:09:07.800 and in my
00:09:09.200 other posts and whatnot. Right now, this
00:09:11.720 strategy here, the GC gold futures
00:09:14.400 directional,
00:09:15.920 works great. Okay.
00:09:18.680 Um so, I can launch it.
00:09:20.880 I could also launch this Ethereum
00:09:22.720 Bitcoin
00:09:24.160 futures spread as well
00:09:26.520 for my testing.
00:09:28.160 Um
00:09:29.800 I'm going to be honest with you, that is
00:09:31.440 a is a pretty good bot um on the win
00:09:35.400 ratio, but the returns are very small
00:09:38.600 and from what I'm showing you
00:09:41.080 on their margin requirement, it's really
00:09:42.960 not worth pursuing.
00:09:44.800 The only one right now that's worth
00:09:46.280 pursuing is this GC gold futures. So,
00:09:48.560 that's all I'm going to focus on right
00:09:50.040 now
00:09:50.920 for live trading, okay?
00:09:53.200 So, we've got this launch, it's running.
00:09:56.000 So, we can have our uh communication log
00:09:58.880 in here.
00:10:00.000 It'll give you all of the information
00:10:01.960 here.
00:10:03.160 Um all the messaging and all of that,
00:10:06.160 okay?
00:10:06.960 I can clear it out, archive, and start a
00:10:08.920 new session
00:10:10.600 as well.
00:10:11.960 Um
00:10:13.040 So, here we can segregate it out.
00:10:16.600 Uh so, you can see here it's connecting
00:10:17.920 to MGC.
00:10:20.440 Okay.
00:10:21.480 And these are messages from the IBKR as
00:10:23.800 well
00:10:25.120 via my TWS Trader Workstation.
00:10:28.800 So, that's the communication log. In
00:10:30.200 here as well, we have uh settings. Now,
00:10:32.800 this is
00:10:33.960 been set up by uh
00:10:36.160 the Floyd 4.7 Opus.
00:10:39.680 Um anyway, so this is what's settings
00:10:42.280 are.
00:10:43.480 Um you can see here
00:10:45.360 doing everything through a browser,
00:10:47.520 through a local host.
00:10:49.360 So, this is using in the server end,
00:10:52.080 it's using um
00:10:54.080 I believe it's been upgraded through the
00:10:55.440 AI
00:10:56.760 for um
00:10:58.760 uh using uh Flask.
00:11:02.160 Okay, so there's that. Um this is the
00:11:04.680 essential for anybody doing
00:11:07.640 uh TWS Trader Workstation or anything
00:11:11.160 Interactive Brokers, make sure
00:11:13.640 if you're testing paper trading, you
00:11:14.960 have to connect into the port
00:11:17.000 7497,
00:11:18.839 okay? But as I said before, the only way
00:11:21.200 to really get this working with proper
00:11:23.120 data
00:11:24.200 through TWS and getting everything
00:11:26.160 subscribed, your subscription set up,
00:11:28.560 blah blah blah, it's it's a real pain in
00:11:30.320 the ass, to be honest, but that's how it
00:11:32.480 is with Interactive Brokers. You do have
00:11:34.680 to set your port at 7496,
00:11:37.600 okay? So, if you need help there, you
00:11:39.720 can just look it up on online or go
00:11:42.520 through YouTube uh
00:11:44.560 tutorial.
00:11:45.880 It'll show you how to do that on the TWS
00:11:47.760 Trader Workstation station software.
00:11:50.520 Um and then there's that. Okay. So, as I
00:11:53.760 said, we've um launched this.
00:11:57.200 Okay. So, we're only running one bot.
00:11:59.960 There's two bots available. At some
00:12:02.000 point I may add in
00:12:04.280 Once I can find a DXY, a dollar index,
00:12:07.040 I'll probably add that as well if if I
00:12:09.080 can find something successful.
00:12:11.760 Um so, here we have our um
00:12:15.920 big big thing here for for um
00:12:19.760 for regulatory reasons. So, if you trade
00:12:22.360 big money,
00:12:23.840 thousands, hundred thousands, millions
00:12:25.600 in fact, and you're trading it through
00:12:27.680 the Aurora exchange through CME in
00:12:30.760 Aurora, Illinois for high-frequency
00:12:32.800 trading, by regulation, you have to have
00:12:35.640 a kill switch in there.
00:12:37.440 And what this will do is whatever open
00:12:39.360 positions there are, you just hit that
00:12:41.600 activate, and it'll flatten out all the
00:12:43.440 positions and close them out
00:12:45.600 to prevent the account from going crazy
00:12:47.520 cuz if you look into
00:12:49.720 the regulatory
00:12:51.440 impact and the fines you can be
00:12:55.120 have imposed upon you if you have
00:12:57.640 some automated strategy bot, whatever,
00:13:01.800 uh going crazy and just losing money,
00:13:04.400 could impact others or the exchange
00:13:06.520 itself. It can happen.
00:13:08.800 Um
00:13:09.800 one guy
00:13:11.160 in uh UK did that with uh through
00:13:14.120 trading technology,
00:13:15.800 and got fined in the millions cuz he did
00:13:17.720 I don't know what he was trying to do,
00:13:18.800 but he got fined heavily. Just one
00:13:20.480 trader, one retail trader through Take
00:13:22.800 Trading Technologies years ago. So, you
00:13:24.160 have to be very careful here. So, you
00:13:26.360 can ask the to to to to implement this
00:13:29.560 kill switch. The best AI as I said is
00:13:32.040 use use Claude, the latest Claude or
00:13:34.320 whatever that.
00:13:36.400 Okay, so we know technically
00:13:39.680 everything seems to be working here as
00:13:42.000 far as I know.
00:13:43.440 Um we can see that as I said through the
00:13:46.720 um
00:13:47.720 the uh
00:13:50.040 through this communication log here.
00:13:52.760 So, um you can see here the volume
00:13:56.240 the bid and ask as well. So, you know
00:13:58.640 that this should be working.
00:14:00.960 Okay?
00:14:02.080 So, there's that.
00:14:03.520 We have uh portfolio performance.
00:14:05.640 There's no trading on this. I'm just
00:14:06.960 showing you
00:14:08.480 the demos. Um this is the interesting
00:14:10.880 ones, the depth of market.
00:14:13.000 So, right now um I'm only watching MET
00:14:17.480 uh micro micro Ethereum
00:14:20.080 micro gold GC
00:14:22.360 and micro Bitcoin. This is real market
00:14:24.640 data
00:14:25.760 coming through
00:14:27.280 um
00:14:28.360 TWS. Okay? So, you can see here high low
00:14:31.680 close, all that information.
00:14:34.600 The interesting one I don't think is
00:14:36.000 really going to be useful. It's not very
00:14:38.800 to do this type of trading or setting up
00:14:40.680 charts
00:14:42.200 it it's pointless to be honest. I just
00:14:43.960 thought I'd put this in here for
00:14:45.160 demonstration purposes.
00:14:47.600 Um but you can supposedly you can
00:14:50.800 probably code it up via AR AI but have
00:14:55.240 all these charts update every minute, 5
00:14:58.320 minutes, whatever you want. It doesn't
00:15:00.160 work all that well, but just to put the
00:15:01.760 extra utilization not worth it.
00:15:04.080 You know, you can watch visual
00:15:05.040 visualization through other platforms,
00:15:07.120 TradingView or
00:15:09.200 some other uh software. You don't really
00:15:11.600 need it that. Um portfolio performance,
00:15:13.839 nothing's being traded as I said.
00:15:16.240 Um
00:15:17.160 and that's pretty well it.
00:15:19.160 Um so, I can start off all the bots up
00:15:20.800 here.
00:15:21.960 Um and I said, we've got the bot
00:15:24.000 control,
00:15:25.200 launch, stop.
00:15:27.200 Um, the live monitor.
00:15:29.240 This is an interesting one as well. This
00:15:31.200 is where you can really see
00:15:33.400 the flaws of Interactive Brokers.
00:15:36.360 Some of the times the status will go
00:15:38.360 into stale or offline.
00:15:41.240 Um, so these may change around cuz it's
00:15:44.520 polling every minute, every
00:15:47.240 2 minutes, whatever the uh TWS allows,
00:15:51.000 and it can conk out anytime it wants for
00:15:54.400 a couple of seconds or even for a
00:15:55.760 minute.
00:15:56.920 Um, you can see that through the status.
00:15:59.040 Once this is running,
00:16:01.000 I'm trading,
00:16:02.320 you can see all these alerts, and that's
00:16:04.080 all coded up in both the
00:16:06.600 Python and the bot itself,
00:16:09.280 um, as well. But, um,
00:16:12.160 it's it's this is as good as I can get
00:16:14.120 it, uh, as it stands,
00:16:16.520 outside of the funding and being able to
00:16:18.720 live trade. Uh, as I said, once I can
00:16:21.520 get that working
00:16:23.160 under the uh last year, the buy ES and
00:16:26.320 the sell ES.
00:16:27.880 If you look at it, there's not enough
00:16:29.240 funding yet, um, for that, and it'll
00:16:32.280 generate an error.
00:16:33.960 Weird error messages from the TWS API,
00:16:37.640 um, and it'll cancel.
00:16:40.000 Uh, and that's how that works.
00:16:43.040 So, generally, this is the whole app.
00:16:44.800 This is
00:16:45.680 pretty sophisticated itself to get it to
00:16:47.800 this point, but I wanted to show you
00:16:50.200 this. Um, I probably will upgrade the
00:16:52.560 Rithmic one.
00:16:54.120 Um, it's To be honest, I think the
00:16:55.839 Rithmic's just better
00:16:58.040 trade.
00:16:59.200 Um, my review of Interactive Brokers is
00:17:01.360 just Here's the thing with Interactive
00:17:03.000 Brokers.
00:17:04.400 Um,
00:17:06.079 so that's the demo.
00:17:07.800 Uh, let me just get back to where I want
00:17:09.920 to go.
00:17:11.439 Okay.
00:17:12.760 So,
00:17:13.880 uh,
00:17:16.319 yeah.
00:17:17.319 So, that's the demo. Uh
00:17:19.160 what I can say about working with
00:17:21.640 Interactive Brokers,
00:17:23.240 it's frustrating and it's not
00:17:24.480 frustrating.
00:17:26.000 To get access to call a human, it used
00:17:28.439 to be you just call 1-800 whatever, and
00:17:30.880 you talk to a new human. Um
00:17:33.880 it's worse and it's better
00:17:36.320 since 2 years.
00:17:37.960 Uh and today, just so people know, is
00:17:39.880 March 20th, uh I'm I'm sorry, May 20th,
00:17:42.960 uh 2026.
00:17:45.200 So, when you call, you can't just call a
00:17:47.680 1-800 for the support now. You have to
00:17:50.360 have
00:17:51.520 an actual
00:17:53.120 ticket created. Now, to create that
00:17:54.880 ticket,
00:17:56.280 you have to go in.
00:17:58.360 Everything's all automated, okay?
00:18:00.720 So, you have to go in, go through the
00:18:03.000 help, no, it didn't help me.
00:18:06.000 And then it'll ask you, can you want to
00:18:07.080 create a ticket?
00:18:09.000 Put the type of problem, the sub
00:18:11.160 problem,
00:18:12.320 create a ticket, and then you get the
00:18:14.280 ticket number. Okay?
00:18:16.600 So,
00:18:17.960 that will activate the Interactive
00:18:20.040 Brokers system.
00:18:22.800 Um so, when you call into the 1-800 to a
00:18:25.920 real human,
00:18:27.320 good thing is, between what I was told
00:18:29.360 today,
00:18:30.320 between trading hours, you will most
00:18:32.480 likely and should get
00:18:34.360 um patched through to a
00:18:37.320 uh
00:18:38.000 a North American call center if it's
00:18:39.800 called US or Canada.
00:18:42.040 And if it's outside hours, there is
00:18:43.640 24-hour support,
00:18:45.400 you will be put through an off-shore
00:18:48.880 um call center. So, I can't guarantee
00:18:50.800 you that.
00:18:52.000 But, um because I was put through a US
00:18:54.480 one,
00:18:55.600 uh Chicago, support was good once I get
00:18:57.960 that that point. When you call the 1-800
00:19:00.400 number, you have to verify
00:19:02.720 yourself through the traditional, the
00:19:05.480 typical
00:19:06.880 uh
00:19:07.960 2FA
00:19:09.640 through the web app or sorry, through
00:19:11.800 the
00:19:12.720 um
00:19:13.680 through the uh most likely if you're
00:19:15.800 using the app, you have to authorize
00:19:18.280 yourself through the phone app.
00:19:20.320 Once you get that, then you can proceed
00:19:22.080 to go into the call.
00:19:24.200 It will also know
00:19:26.200 about your open tickets. So,
00:19:29.000 it will say, &quot;Here's this most recent
00:19:31.400 ticket.&quot; Once you opened it,
00:19:33.520 I just put in some blurb in there. Uh
00:19:36.400 then it knows that you created a ticket,
00:19:38.600 you made whatever effort,
00:19:40.680 uh you can then get passed through to an
00:19:42.520 actual human. So, that's how it works
00:19:44.600 now. So, in a way it's kind of a pain in
00:19:47.320 the butt
00:19:48.880 to get to that point.
00:19:50.560 Um but read the ticket through the
00:19:53.120 portal. Okay? You ask questions through
00:19:55.520 their bot thing.
00:19:57.480 You can't find it. You will see an
00:19:59.200 option, &quot;Did this help you?&quot; No.
00:20:01.880 Then it'll ask you, &quot;Do you want to
00:20:02.800 create a ticket or get further support?&quot;
00:20:04.720 Yes.
00:20:06.040 And create your ticket. And just put
00:20:07.840 your one-line blurb in there. And then
00:20:09.480 once you call in the 1-800 number,
00:20:12.080 uh in North America, you should be able
00:20:13.800 to get into human. And once you get
00:20:15.480 there, then it can
00:20:17.440 then it seems to be better than better
00:20:19.320 than when you actually talked to human
00:20:20.640 back in the day,
00:20:21.920 few years ago.
00:20:23.120 Um so, that's pretty well it.
00:20:25.040 Um
00:20:26.720 I still got to get my account tested.
00:20:29.360 As I said, with all the different um
00:20:32.480 options out there for trading.
00:20:35.760 Um the only one worthwhile right now
00:20:38.920 outside of crypto
00:20:40.600 because the crypto um requirements are
00:20:43.360 quite
00:20:44.800 big.
00:20:45.960 Uh you're going into thousands upon
00:20:47.960 thousands of dollars to make any's. Not
00:20:50.680 worth it right now, at least for my type
00:20:52.640 of strategy.
00:20:54.080 Um
00:20:55.320 but with the gold, yes, there is
00:20:58.440 potential there. And that's all I'm
00:21:00.360 going to really focus on. As I said, if
00:21:02.600 when I can find
00:21:04.280 a dollar It's connection loss the XY
00:21:06.760 strategy, I will definitely focus on
00:21:09.280 that as well. I've also seen a Euro
00:21:12.040 >> reestablished.
00:21:13.800 >> So, chances are I don't know if I'm
00:21:16.080 going to be focusing on crypto because
00:21:18.360 of this margin requirement and the very
00:21:20.200 little return I get for it.
00:21:22.360 I don't know if it's worthwhile um
00:21:24.320 because of the crazy
00:21:26.200 volatility. You're better off to put it
00:21:27.760 into maybe a Bitcoin ETF you feel
00:21:31.880 compelled to do that. Um also for
00:21:34.360 Canadians
00:21:35.880 Canadians cannot trade retail crypto
00:21:39.040 through their Paxos option. US they can.
00:21:42.320 Uh it sounds like that's pretty
00:21:44.280 uh
00:21:45.360 regulatory is pretty tight on that. Uh
00:21:47.640 but I can trade uh crypto, Bitcoin,
00:21:50.120 Ethereum and the like on
00:21:52.200 the market via obviously the CME. So,
00:21:54.680 that can be done, too.
00:21:56.360 All right, so we're done. So, as I just
00:21:58.480 said, if you want to get more
00:22:00.960 information, I would probably opt into
00:22:03.480 my email list as well.
00:22:05.960 Um let me just go back to the screen
00:22:08.240 here.
00:22:10.960 So, if you want to get more
00:22:13.400 info and you like what you see,
00:22:16.280 what I would recommend is just go to the
00:22:17.760 quantlabs.net.com
00:22:20.000 website here and sign up right here to
00:22:22.280 get on your my email list, get a little
00:22:24.520 e-book, blah blah blah.
00:22:26.440 Um I do streams now and a lot of people
00:22:29.320 want to know where to start. And the
00:22:31.080 thing where I point them to, and I've
00:22:33.360 mentioned this many times,
00:22:35.240 all my
00:22:36.480 streams, all the same thing. If you want
00:22:38.840 to get started, you get started this
00:22:40.040 website I I just put up a few months
00:22:42.080 ago.
00:22:43.200 hftcode.com. There could be two paths
00:22:45.800 you can go down.
00:22:47.040 The general path where I just showed you
00:22:48.760 with the IBKR,
00:22:50.680 this little bot thing right here,
00:22:53.440 includes a bunch of PDFs that will help
00:22:56.520 you.
00:22:57.480 Um it will have working code for
00:23:00.840 different strategies for Forex, for
00:23:04.000 um couple of stocks. So, you can you can
00:23:06.720 use that. They work.
00:23:08.640 And then some of the PDFs will tell you
00:23:10.360 how to prompt and build out things to
00:23:13.280 what I've shown you with that demo app.
00:23:15.960 Um
00:23:18.200 you could probably vibe code it if you
00:23:20.080 could.
00:23:21.240 Um to be honest,
00:23:23.960 uh
00:23:24.800 um you could probably do something
00:23:26.520 pretty basic, but you still got to be a
00:23:28.200 fairly accomplished
00:23:30.160 uh developer uh as well. So, as an
00:23:32.920 example, uh to try to put a trade
00:23:35.440 through, it'll say
00:23:37.480 uh has to be a float, not a number. You
00:23:39.880 have to know the difference.
00:23:41.760 With a float being
00:23:43.360 decimal point point zero or whatever
00:23:45.960 number of contracts. If you don't know
00:23:48.560 the basics of programming and trying to
00:23:50.920 get through that, your AI probably won't
00:23:53.200 be able to fix that, just so you know.
00:23:55.720 Uh the other path is if you want to get
00:23:57.560 into quant coding, quant generally is a
00:24:00.160 career.
00:24:01.360 Same product, it's 20 bucks more. I give
00:24:04.200 extra PDFs
00:24:06.400 that will walk you
00:24:08.480 through um Citadel,
00:24:11.520 Two Sigma, RenTech, and so on, about
00:24:14.360 seven firms.
00:24:15.840 Each firm looks for different
00:24:17.760 requirements out of their candidates.
00:24:19.720 And the AI
00:24:21.600 will show you typical role play
00:24:23.320 questions that you can use
00:24:25.760 as well. So, you can you can get that
00:24:27.280 there.
00:24:28.240 All right. So, that is pretty well what
00:24:30.680 I want to show you.
00:24:32.160 Okay? It's a lot to take in, I I know.
00:24:35.400 Um Rithmic is much more fun. So, I'll
00:24:38.000 just leave it at that.
00:24:39.640 But I just want to get the funding. I'm
00:24:41.640 going to keep it prim and proper for
00:24:44.200 the beginning. And as I said, just focus
00:24:46.840 as minimum as I can from the funding
00:24:48.680 aspect to reduce risk
00:24:51.040 and just focus on gold. That's all I can
00:24:53.400 do right now. As I said in my stream
00:24:54.840 from last night,
00:24:56.520 and uh we'll leave it at that. And
00:24:58.080 thanks for watching. Have a good day.

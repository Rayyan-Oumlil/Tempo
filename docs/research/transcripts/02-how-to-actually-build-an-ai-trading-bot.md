
# tactiq.io free youtube transcript

# how to actually build an ai trading bot (full guide)

# https://www.youtube.com/watch/PBBSMSyU674

00:00:00.000 I'm going to show you how to build a
00:00:01.800 trading bot that actually works, whether
00:00:04.240 you trade crypto or stocks. I'm going to
00:00:06.400 run you through how to build one from
00:00:08.080 scratch and what they're actually good
00:00:10.320 for because it's not what most people
00:00:12.120 think. You've probably seen the promises
00:00:13.840 that AI trading bots are like these
00:00:15.560 magic money printers, but the reality is
00:00:17.760 different. They can be highly
00:00:19.040 profitable. I've personally built
00:00:20.440 strategies which have made me over
00:00:22.200 $8,000 a week in pure profit, but I've
00:00:25.520 also had trading bots, especially
00:00:27.520 towards the beginning of my journey a
00:00:28.880 few years ago, which went horribly wrong
00:00:30.880 and cost me tens of thousands of
00:00:32.640 dollars. But, I learned from those
00:00:34.080 mistakes and learned how to set up
00:00:35.880 trading bots the right way, bots that
00:00:37.720 automatically get smarter over time and
00:00:39.760 bots that don't fail. The best part is
00:00:42.000 you don't have to be a coder for any of
00:00:43.800 this. It's actually quite simple. You
00:00:45.560 just might need to get your hands a
00:00:47.120 little dirty, but I'm going to walk you
00:00:48.640 through step-by-step so you don't get
00:00:49.960 lost. And by the end, you'll know how to
00:00:52.160 actually build a trading bot that works.
00:00:54.360 And you'll also know the one mistake
00:00:55.920 that kills people's trading bots so you
00:00:58.360 don't make it. All right, firstly, let's
00:01:00.440 talk about what an automated AI trading
00:01:02.840 bot actually is. A bot essentially does
00:01:05.400 two things. It automates repetitive
00:01:07.440 strategy and it executes better than a
00:01:09.760 human. I used to find in my trading, I'd
00:01:11.960 have the right ideas, but I'd have an
00:01:13.880 execution problem. I'd have a setup, but
00:01:16.240 I wouldn't be at the desk to execute the
00:01:17.960 trade. I wouldn't be able to manage the
00:01:19.760 trade once it's open or I would simply
00:01:21.720 forget to manage the trade and that
00:01:23.200 would result in me losing money. The
00:01:25.040 real value add of a trading bot is that
00:01:27.880 it can execute based on a predetermined
00:01:30.040 strategy that you've given it. And the
00:01:31.880 really important thing which we're going
00:01:32.960 to discuss today is that these bots
00:01:34.840 actually learn over time and they get
00:01:36.600 smarter over time. They learn from their
00:01:38.440 mistakes probably even better than a
00:01:39.960 human because it's coded into the AI.
00:01:42.520 Whereas as a human, you need to go
00:01:44.120 through a lot of psychological
00:01:45.440 reflection to work out why maybe you're
00:01:47.760 not succeeding as a trader. So,
00:01:49.320 ultimately, I view trading bots as a way
00:01:51.080 to get razor sharp execution and I do
00:01:53.240 think over time more and more people are
00:01:55.600 going to be using trading bots and in a
00:01:57.280 few years pretty much everyone will be
00:01:59.320 using one whether they know it or not
00:02:01.320 because the big funds and the quant
00:02:02.640 firms, they are already doing this.
00:02:04.640 Retail just isn't fully up to scratch
00:02:06.360 yet. The best part about a bot is that
00:02:08.038 it doesn't flinch, it doesn't get
00:02:09.360 scared, it can execute without emotions
00:02:12.200 and that's what actually catches most
00:02:13.600 traders out. So if your problem was ever
00:02:15.280 execution as it is for most people, then
00:02:17.640 building a trading bot should really
00:02:18.800 help you. And the loop of a trading bot
00:02:20.360 is actually quite simple. You set up the
00:02:22.320 parameters, it executes based on those
00:02:24.320 parameters, it learns from those
00:02:25.959 parameters and then it goes again. And
00:02:27.800 this loop can automate around the clock
00:02:29.280 24/7 even while you're sleeping. And
00:02:31.920 some of my bots where I've made over
00:02:33.560 $8,000 in a week, these have actually
00:02:35.360 executed some of my best trades when I
00:02:37.440 wasn't awake. Especially if you're not
00:02:39.600 available all day or not on US hours, I
00:02:41.560 think that's one of the biggest value
00:02:42.880 props of automating your trading. But I
00:02:45.200 want to make it clear this isn't a magic
00:02:46.840 fix. I do think this stuff is getting
00:02:48.680 better and better and being at the
00:02:50.120 cutting edge of it like I'm trying to is
00:02:51.800 a big advantage, but this isn't a full
00:02:54.160 replacement for discretionary trading. I
00:02:56.040 view trading bots as a great attachment.
00:02:58.000 So you can have discretionary ideas,
00:03:00.000 ideas that you think will help you get
00:03:02.200 an edge in the market and then you use a
00:03:04.239 trading bot for the execution piece.
00:03:06.640 That's pretty much how I use them in my
00:03:08.720 day-to-day life. And then over time, you
00:03:10.880 can start to knowledge compress. So take
00:03:12.840 strategies from yourself and from others
00:03:15.120 that you want to implement and train the
00:03:16.840 AI to do so automatically. So before we
00:03:19.080 get into how to build a winning trading
00:03:20.560 bot, let's firstly discuss why most
00:03:23.000 trading bots lose. They're usually four
00:03:25.120 reasons why trading bots lose money. The
00:03:27.000 first one is they don't have memory. So
00:03:29.320 basically it'll open a trade or it'll
00:03:31.560 execute something based on its preset
00:03:33.400 parameters, but then it doesn't learn,
00:03:35.239 improve, and iterate over time. I'll be
00:03:37.120 showing you a memory system in today's
00:03:38.560 video which pretty much makes that
00:03:40.480 mistake irrelevant. Secondly, people set
00:03:42.800 up trading bots with no goals or no
00:03:44.600 objectives. So they'll set a test, but
00:03:46.920 they won't define the parameters for
00:03:48.440 that test. So then you're basically
00:03:49.959 trading blindly. The bot isn't getting
00:03:52.040 smarter, the bot isn't necessarily
00:03:54.520 optimizing, it's just running on its own
00:03:56.680 accord. So, without a goal and an
00:03:58.360 objective and without actually
00:04:00.200 implementing that data, it's basically
00:04:02.360 just winging it. The third reason bots
00:04:03.920 fail is because they don't take into
00:04:06.040 account future conditions. Bots are
00:04:07.920 trained on past data. So, you need a
00:04:10.200 good system to forecast data and some of
00:04:13.720 that is discretionary. Some of that
00:04:15.200 can't be automated, but you can
00:04:16.680 obviously build good market scraping
00:04:18.680 systems to plug into the bot to give it
00:04:20.959 more informed information. Human traders
00:04:23.040 can be very good because they adapt to
00:04:24.720 the market very quickly and humans have
00:04:26.880 like this creativity element that bots
00:04:28.720 don't have. We can actually forecast
00:04:30.360 data. Whereas AI models in general,
00:04:32.480 they're all trained on past data. So,
00:04:35.080 you actually need to manufacture things
00:04:36.960 and you can use that to your advantage,
00:04:38.400 but you have to set things up properly
00:04:40.480 so the AI can actually execute based on
00:04:43.040 future expectations. And fourthly, the
00:04:45.040 reason why a lot of trading bots fail is
00:04:46.880 because a lot of the pre-packaged bots
00:04:48.680 simply too many people are using. So,
00:04:50.240 they actually lose their edge in the
00:04:51.680 market. So, if you just go out and buy a
00:04:53.240 popular bot that hasn't been backtested,
00:04:55.520 that doesn't have an edge, you're
00:04:57.000 probably going to be competing against
00:04:58.560 other traders running the same strategy.
00:05:00.640 So, it's important to work out your own
00:05:02.520 strategy or use a bot that millions of
00:05:04.680 people aren't using. In my opinion, to
00:05:06.760 summarize what makes a good bot, it
00:05:08.600 remembers, it gets smarter over time and
00:05:11.320 it's actually yours. So, it's
00:05:12.480 configurable based on your beliefs and
00:05:15.680 based on the data that it accrues. So,
00:05:17.880 now you know why most trading bots fail
00:05:19.960 and you know what constitutes a good
00:05:21.560 trading bot in my opinion. Now, let's
00:05:23.080 move on to your options. What is
00:05:24.640 currently available in the market right
00:05:26.400 now for you to use? Now, there are a few
00:05:29.000 and they all make sense for different
00:05:30.440 people and different skill levels. So,
00:05:32.280 let's run through them. Firstly, you can
00:05:33.760 buy a ready-made AI bot. These are maybe
00:05:36.120 some of the bots you've seen advertised
00:05:38.000 on some platforms or built into an
00:05:39.880 exchange with pre-configured parameters.
00:05:42.320 These aren't necessarily bad. In fact,
00:05:44.040 they don't require any effort, so that
00:05:45.760 is a good thing from a setup and time
00:05:47.480 perspective, but ultimately you don't
00:05:48.880 have your own edge because it's a black
00:05:50.440 box. You don't know exactly how they're
00:05:52.200 trained, and even if their algorithm is
00:05:53.960 public, you have no ability to influence
00:05:56.240 that algorithm. So, you're at the behest
00:05:58.040 of the platform that you are using. Good
00:06:00.080 option for people just trying to dip
00:06:01.680 their toes in the water and maybe use a
00:06:03.520 trading bot on an exchange, but maybe
00:06:05.640 not so good for people that want proper
00:06:07.760 customization, which I do believe is
00:06:10.040 very important because the way that you
00:06:11.600 run your portfolio or your trading is
00:06:13.560 going to be different from how I run my
00:06:15.280 portfolio or my trading. So, we need our
00:06:17.560 bots to reflect the very unique
00:06:19.600 differences in both of our goals, and
00:06:21.520 the only way to do that is through
00:06:22.680 customization, which brings me on to
00:06:24.840 point two. You can use a no-code
00:06:26.600 platform. So, this is a platform that
00:06:28.840 gives you some customization, but isn't
00:06:30.919 a full black box. So, you've got
00:06:32.400 Composer for stocks. You've even got
00:06:34.320 Robinhood now who launched their agents.
00:06:36.200 You don't have full control, and they
00:06:37.800 don't make it open source for you to
00:06:39.480 necessarily connect an API and do things
00:06:41.720 yourself on their exchange. Maybe
00:06:43.560 they'll add it in the future, but for
00:06:44.760 now, you're limited to the options that
00:06:46.680 they're giving you. These are definitely
00:06:47.960 better than the previous option, but I
00:06:50.200 do feel like you're going to hit your
00:06:51.440 ceiling fast, and it's going to limit
00:06:53.400 your ability to progress over time. But,
00:06:56.000 I'm definitely still experimenting with
00:06:57.480 some of these, and I think for some
00:06:58.840 traders it makes sense. Like, setting up
00:07:00.240 a grid bot, setting up DCA bots, setting
00:07:03.000 up basic portfolio management based on
00:07:05.480 preset parameters. It makes sense for
00:07:07.320 some people, but for people that want a
00:07:09.080 fully autonomous strategy, you're going
00:07:10.720 to cap out with these types of systems.
00:07:12.560 And thirdly, this is something that
00:07:14.320 previously used to take months to do,
00:07:16.160 but now you can do relatively quickly,
00:07:17.840 as I'm about to show you, you can build
00:07:19.720 your own trading bot where you actually
00:07:21.760 own the memory system, own the data, and
00:07:24.200 own the configurability. It's actually
00:07:26.120 pretty wild to think that you can now
00:07:27.960 have like an AI quant in your pocket,
00:07:29.880 essentially, that can trade on your
00:07:31.320 behalf 24/7. When, you know, previously
00:07:33.960 this stuff was only reserved for the
00:07:35.840 elite, and that's what these new
00:07:37.760 frontier models like Claude and GPT have
00:07:40.240 now unlocked. And many exchanges and
00:07:42.720 brokerages have actually embraced this
00:07:45.120 cuz they understand users are using
00:07:46.800 these products. So, we're actually going
00:07:48.440 to create MCPs, which are the bridges
00:07:50.920 between Claude and the exchange to
00:07:53.440 enable you to automate your trading. And
00:07:55.880 this has only really happened in the
00:07:57.000 last couple of months. Like I've been
00:07:58.520 using trading bots for 3 years, but it
00:08:00.600 was only really this year that you could
00:08:02.800 fully customize a bot. So, you're
00:08:04.640 actually really early to this. If you're
00:08:05.920 watching the video right now, make sure
00:08:07.400 you subscribe to the channel cuz I'm
00:08:08.560 going to keep updating you as things
00:08:10.440 evolve because I think in the next
00:08:11.920 couple of years things are just going to
00:08:13.120 get better and better and better. So,
00:08:14.680 I'm pouring a lot of time and resources
00:08:17.080 into making sure I can get an edge with
00:08:18.640 this kind of stuff. And I want you guys
00:08:20.240 to come on this journey with me as well
00:08:22.080 because I have a clear thesis that this
00:08:23.640 is where the world is heading. I think
00:08:25.480 in the future we're heading towards a
00:08:27.000 world where people don't just go into
00:08:28.200 the computer or grab their phone and
00:08:30.080 place a trade manually. I think people
00:08:32.679 will be voice prompting agents. I think
00:08:34.159 agents will be managing portfolios on
00:08:35.640 their behalf. And I think the way you
00:08:37.000 interact with exchanges and trading will
00:08:39.000 be very, very different. want to be at
00:08:40.679 the forefront of that. So, now I'm going
00:08:42.000 to give you the three-step approach to
00:08:44.039 actually build your own trading bot. And
00:08:46.000 if somehow you get lost at any point,
00:08:47.480 don't worry. In the description below
00:08:49.440 for free, I'm going to have the full
00:08:51.160 framework from today's video that you
00:08:53.080 can actually just take and paste into an
00:08:55.720 LLM like Claude or ChatGPT, and it will
00:08:58.280 actually help you execute on your
00:09:00.680 behalf. So, all you need to do is go
00:09:02.760 down below, enter your email, become a
00:09:04.800 part of the newsletter, and then you
00:09:06.160 will unlock the WhatsApp community where
00:09:08.120 in the pinned link you will be able to
00:09:10.440 find the prompt from today's video. All
00:09:12.880 right, so let's get into the three
00:09:13.960 steps. So, step one, picking your venue.
00:09:16.520 Firstly, you want to determine what
00:09:18.120 you're trying to trade. Is it stocks or
00:09:19.800 is it crypto? And crypto now obviously
00:09:21.720 has access to tokenized stocks and gold
00:09:24.400 and these sorts of things as well, even
00:09:26.440 perps trading. So, a lot of people that
00:09:28.640 are trading stocks are now doing it
00:09:29.960 through hyperliquid or through X
00:09:32.520 tokenized stocks, but obviously that
00:09:33.920 comes with its own trade-off. So, first
00:09:35.440 and foremost, you want to pick which
00:09:37.280 lane you're most interested in. So,
00:09:38.640 here's the broader architecture for a
00:09:40.040 trading bot, no matter if it's stocks or
00:09:42.440 crypto. The brain is going to be your
00:09:44.440 LLM. So, in this case, Claude. You can
00:09:46.560 also use GPT. So, you're either using
00:09:48.600 Claude code on the newest model, or
00:09:50.600 you're using GPT's CodeX on the newest
00:09:52.600 model. That brain is responsible for
00:09:54.360 holding and executing your strategy. The
00:09:57.080 hands, what actually delivers the
00:09:59.160 information to the exchange that's
00:10:00.880 executing the trades, or you can think
00:10:02.800 of it as a bridge, is the MCP server.
00:10:05.560 That's the piece that actually enables
00:10:07.320 Claude to place real orders on an
00:10:09.880 exchange or a brokerage. And not every
00:10:12.120 single brokerage has a connection, but
00:10:14.160 there are a couple really good ones that
00:10:15.560 I'll tell you today. For stocks, I
00:10:17.600 personally use Alpaca, because they have
00:10:20.000 an MCP server, which makes this easy.
00:10:22.160 And this video's not sponsored by
00:10:23.200 anyone, by the way. These are just the
00:10:24.360 best solutions that I've personally
00:10:25.800 found. It's free, it has paper trading,
00:10:28.200 which is amazing, because you want to
00:10:29.440 test this stuff out if you're learning
00:10:31.080 on fake money. You don't want to go and,
00:10:32.880 you know, blow real money and mess up a
00:10:34.280 configuration. The best way to actually
00:10:35.960 get started with trading bots is to do
00:10:37.920 paper trading. Once you're comfortable,
00:10:39.960 and once your strategy's working, then
00:10:41.920 you move on to a bit of real money, and
00:10:43.560 then you keep leveling up. But
00:10:44.680 essentially, you sign up for an Alpaca
00:10:46.040 account, you grab your API keys, you
00:10:48.320 give Claude the API, and then it uses
00:10:50.200 their inbuilt MCP. It might sound
00:10:51.960 complex, but honestly, it's easier than
00:10:53.440 it sounds. The prompt that I'll give you
00:10:54.920 will make this super easy, and Claude
00:10:56.800 will just guide you through the whole
00:10:57.960 process. And that's the benefit of using
00:11:00.080 a platform that has an inbuilt MCP, so
00:11:02.360 you don't have to build your own. You're
00:11:03.440 not actually coding a connection, you're
00:11:05.120 just plugging it in. This gives Claude
00:11:06.839 the capability to pull live prices from
00:11:09.760 the exchange and execute trades based on
00:11:11.839 your strategy. For crypto, it's the
00:11:13.400 exact same concept. You want to go
00:11:15.320 straight to a crypto exchange. There are
00:11:17.200 so many. Binance, Blofin, Bybit, Pionex.
00:11:21.280 Pionex and a lot of other exchanges now,
00:11:22.960 for example, have an inbuilt MCP that
00:11:25.839 you can use, just like Alpaca, so you
00:11:27.800 can connect the MCP to Claude. If you go
00:11:30.000 into to websites, they're usually
00:11:31.920 available. If not, you can just ask
00:11:33.800 Claude to help you connect the
00:11:35.480 exchanges. Then you need to go into the
00:11:37.400 exchange, take the API key, put it into
00:11:39.800 Claude, and usually after 10 to 15
00:11:42.400 minutes, you'll be able to connect the
00:11:44.160 two, even if the exchange doesn't have
00:11:46.120 an inbuilt solution, which does make
00:11:47.720 things quicker and more secure, but you
00:11:49.800 can still use an exchange without an MCP
00:11:52.160 if you work around it on Claude code.
00:11:54.720 You can also use GPT for this. I think
00:11:56.520 both are good. There's arguments that
00:11:58.240 GPT is smarter or more reliable for
00:12:00.080 coding now. So, I personally use a
00:12:01.320 mixture of both, but I found Claude to
00:12:03.280 be pretty good as long as you give it
00:12:04.720 the right parameters, which we'll also
00:12:06.080 discuss, cuz that's obviously the secret
00:12:07.840 to creating a really good trading bot.
00:12:09.440 One thing on safety, you want to make
00:12:11.400 sure your funds, especially if you're
00:12:13.240 connecting it through an MCP using an
00:12:15.600 API, in case your keys are exposed, in
00:12:17.600 case you lose your device or something,
00:12:19.000 that you actually create a sub account
00:12:20.800 that only has a certain amount of funds
00:12:23.000 that you're willing to give the bot
00:12:24.520 access to. And a lot of exchanges
00:12:26.360 actually have paper trading just like
00:12:27.800 Alpaca, so you can actually just paper
00:12:30.040 trade and test out your strategies, make
00:12:31.920 sure they work, harden security over
00:12:33.840 time before you move on to real capital.
00:12:36.040 I think humans just learn the best by
00:12:37.760 doing. So, if you're able to set this up
00:12:39.520 yourself with paper trading, that's
00:12:41.440 ultimately going to be the best tuition,
00:12:43.480 and I think it's definitely worth the
00:12:44.640 time. Step two, you want to actually
00:12:46.920 pick your strategy and define the
00:12:48.960 feedback loop. So, before any prompt,
00:12:51.240 like open this trade for me, open trade
00:12:53.160 under these parameters, you need to
00:12:55.720 actually define the strategy. Because
00:12:57.480 remember, the bot is only as good as the
00:13:00.000 parameters that it runs under. Now, this
00:13:01.440 is a rabbit hole in itself, and I'm
00:13:02.920 going to do future videos on back
00:13:04.800 testing strategies, the best strategies.
00:13:06.839 This is an entire concept for another
00:13:08.839 time, but in the beginning, you want to
00:13:10.839 start with a pretty simple strategy just
00:13:13.080 to get used to the mechanics of running
00:13:15.880 a trading bot. The best part is that you
00:13:17.360 can actually just back test strategies
00:13:19.080 now, especially now that Claude and
00:13:21.240 TradingView actually have an MCP
00:13:23.640 connection. You no longer have to do it
00:13:25.440 manually on Pine Script. You can just
00:13:27.480 connect Claude to TradingView. I did a
00:13:28.880 video on it, go and watch it that
00:13:30.320 actually shows you how to set this up
00:13:32.400 and then you can just start back testing
00:13:33.960 any strategy. Hey, what if the RSI hit
00:13:36.160 this level and momentum did this? Hey,
00:13:38.040 what if price spikes X% in a day, what
00:13:40.200 happened if you opened a trade every
00:13:41.680 time over the past 3 months? It'll tell
00:13:43.960 you how much you would have made. So,
00:13:45.160 I'd recommend back testing first, taking
00:13:47.480 a strategy which looks to be reliable
00:13:49.800 and then using that strategy to start
00:13:52.680 your trading bot experiment. And of
00:13:54.120 course, you can just go back and forth
00:13:55.800 with the AI about your trading style,
00:13:58.000 your investment philosophy, what
00:13:59.760 strategy you want to follow. Like I
00:14:01.440 recommend before people even set up a
00:14:03.360 trading bot, they do a bit of a back and
00:14:05.280 forth to create a one-page document that
00:14:07.960 they put in the instructions folder of
00:14:10.520 GPT or Claude so the AI actually knows
00:14:13.520 about you, your financial situation, and
00:14:16.320 your goals. I think it's also okay to
00:14:17.920 run a completely separate AI test, but
00:14:20.200 if in the future you do want to make
00:14:22.280 these strategies as I guess we're all
00:14:23.800 aspiring to do, work within the broader
00:14:26.000 context of your goals and your
00:14:27.160 portfolio, then obviously you're going
00:14:28.760 to need to create the documentation for
00:14:30.560 that so the AI can tweak the strategy
00:14:32.480 based on that. For this video, I'll show
00:14:33.880 you a very simple build that I'm using.
00:14:35.720 It's essentially a moving average
00:14:37.040 crossover. So, if we see a fast average
00:14:38.960 crossing above the slower average, that
00:14:41.680 indicates that momentum is increasing.
00:14:44.040 That is our signal to buy. If it crosses
00:14:45.920 back below, we're going to sell.
00:14:48.240 Obviously, over time, you want to create
00:14:50.120 parameters across what time frames,
00:14:52.320 adding in other conditions, and the AI
00:14:54.160 will learn over time, but I'm just
00:14:55.960 showing this to you as an example. This
00:14:57.920 is simple on purpose because this
00:14:59.640 video's about the system. In future
00:15:01.280 videos, make sure you subscribe, we'll
00:15:02.839 dive deeper into the best strategies,
00:15:05.960 but I want to make sure you have a full
00:15:07.160 understanding today of what trading bots
00:15:08.680 are. Of course, we'll just swap in a
00:15:09.960 better strategy later. So, now that you
00:15:11.480 have the idea, you can prompt Claude or
00:15:13.520 GPT to build it. It'll define every
00:15:15.440 interval. The bot will read its memory
00:15:17.640 and check the market through the MCP,
00:15:19.640 and it will apply your rule to open
00:15:21.440 trades, and obviously place paper trades
00:15:24.080 in this example if it fires. So, a bot
00:15:26.200 essentially has three jobs. It sees the
00:15:27.840 market, but it decides whether it wants
00:15:29.400 to execute, and then of course, if the
00:15:31.480 parameters hit, it executes. You can see
00:15:33.440 with this bot, it actually fired on the
00:15:35.520 signal, but the trade loses.
00:15:38.120 And then the same signal shows up again,
00:15:39.680 and then it did the same trade again,
00:15:41.280 but it loses again.
00:15:42.920 This is because, and this is a common
00:15:44.960 issue with bots, it has no memory. So,
00:15:47.000 it never kept score of what's working,
00:15:48.920 or critically reflected on why it's not
00:15:51.160 working. So, this right here is an
00:15:52.600 example of a bot that doesn't remember
00:15:54.080 its own trades. So, it keeps repeating
00:15:55.960 the same mistake. Every single time that
00:15:57.440 parameter hits, it'll just execute
00:15:59.160 because you've told it to execute. What
00:16:00.680 I'll show you now, step three, is going
00:16:03.000 to give your bot real memory, so it
00:16:05.240 self-improves over time. This is the
00:16:07.200 step that really matters, and we create
00:16:09.200 this through a two-file system. File one
00:16:11.640 is going to be your ledger. It's going
00:16:13.120 to log every single trade. It's going to
00:16:15.160 show you what happened, when it
00:16:16.360 happened, why it fired, and how it
00:16:18.840 ended. And you'll actually be able to
00:16:20.120 prompt and reflect on this data. The
00:16:21.880 second file is going to be the learnings
00:16:23.960 file. So, when a trade closes, the bot
00:16:26.440 writes itself one plain English lesson.
00:16:28.839 So, it lost on this setup, don't take it
00:16:30.720 again without confirmation of XYZ. This
00:16:33.120 really matters because every single time
00:16:34.800 it trades, it's going to read the ledger
00:16:36.720 and the learnings file, and then if it
00:16:38.640 makes a mistake again, it's going to add
00:16:40.920 to it. So, this is essentially giving
00:16:42.520 the bot a brain that learns over time,
00:16:44.640 just like a human does. So, if you're a
00:16:46.160 trader, you'll know you get these
00:16:47.880 intuitions, like, &quot;Oh, I think the
00:16:48.839 market's going to crash. I think the
00:16:50.280 market's probably going to go up.&quot; You
00:16:51.640 might not be aware of it, but that's
00:16:52.720 your mental algorithm based on past data
00:16:54.800 that you've analyzed coming into
00:16:56.680 account. You we're just engineering the
00:16:58.280 exact same thing for the AI, but the
00:17:00.120 best thing is, the AI will never make a
00:17:01.880 mistake. Once you train it and set hard
00:17:03.760 rules, it'll stick to those rules. Now,
00:17:05.480 obviously, I've got to make it clear,
00:17:06.640 sometimes AIs do hallucinate. Sometimes
00:17:09.079 it'll break its rules, because these
00:17:10.599 things aren't perfect, but having an
00:17:12.599 understanding of how to set this up now
00:17:14.359 is extremely beneficial, because in the
00:17:16.400 future months and future years, these
00:17:18.280 things will get near perfect. We know
00:17:20.119 we're heading towards a world where AIs
00:17:22.040 are smarter than us, more accurate than
00:17:23.400 us, even though they might make some
00:17:24.839 mistakes now. I mean, just look at how
00:17:26.560 far they've come since I started using
00:17:28.160 trading bots a few years ago. Like, they
00:17:29.560 are already so much better and they'll
00:17:31.080 keep getting better. So, if there are
00:17:32.600 issues, just persist. It can be
00:17:34.560 frustrating, but that's actually how you
00:17:36.360 learn and create better bots over time.
00:17:38.280 Now, for the more advanced people, two
00:17:40.400 files is okay to start. That is a
00:17:41.880 workable memory system, but you may want
00:17:44.040 to consider building a cloud memory
00:17:46.000 system on something like Superbase or
00:17:49.440 Supermemory or Firebase where your
00:17:51.840 memory is actually stored on the cloud.
00:17:54.120 So, it's the exact same idea, but it's
00:17:55.960 actually a database instead of just
00:17:57.560 files, so it can hold thousands of
00:17:59.960 trades and a much bigger ledger that
00:18:02.640 will be less intensive for the bot to
00:18:05.640 review. Especially if you're a
00:18:07.120 high-frequency trader, you're probably
00:18:08.880 going to need to upgrade from the true
00:18:10.240 file system after a few weeks of trading
00:18:12.440 cuz you'll have so much data and it will
00:18:14.160 actually slow your AI down. So, this
00:18:16.120 time I'm doing a test where I gave the
00:18:18.240 bot some memory. I set up this system
00:18:20.880 and if you actually run it again, the
00:18:22.920 losing signal shows up, but this time
00:18:25.800 the AI actually checks its own record.
00:18:28.320 It sees it already lost on a similar
00:18:29.840 setup to this, so it decides to skip it.
00:18:31.920 This is the key. It's not just being
00:18:33.920 cautious, it still takes good setups,
00:18:36.000 but it skips the one that it loses from
00:18:38.400 in the past. So, if you look at the two
00:18:39.960 side by side, the bot with no memory
00:18:41.880 just keeps bleeding on the same trade,
00:18:43.840 but the one that remembers stops the
00:18:45.520 bleeding and keeps the winning trades.
00:18:47.720 Now, imagine this iterating over
00:18:49.480 thousands of trades, it just gets
00:18:51.160 smarter over time. So, that's the same
00:18:53.600 strategy, but memory is the key
00:18:55.120 differentiator there. But now, let's
00:18:56.720 talk about the honest reality. Before
00:18:59.280 you run a bot with real money, before
00:19:00.800 you just copy a random strategy, make
00:19:03.160 sure that you test something with paper
00:19:04.920 money first. I'm going to give you some
00:19:06.080 homework. Go away, take the prompt from
00:19:08.240 today's video available in the
00:19:09.360 description below, build your own
00:19:10.880 trading bot whether it's for crypto or
00:19:12.600 stocks, and paper trade for a week, and
00:19:15.600 learn to refine your memory system. Once
00:19:18.000 you're confident, then start with a
00:19:19.760 little bit of money, maybe 1, 2, 3% of
00:19:22.120 your max risk tolerance, and then scale
00:19:24.440 up over time. The majority of your
00:19:26.400 losses are going to come in the early
00:19:28.200 days as you're still figuring things out
00:19:30.480 and as the bot is figuring things out,
00:19:32.320 and things only become reliable as
00:19:34.720 things develop over time. I'm going to
00:19:36.640 be backtesting a lot of strategies on
00:19:38.200 this channel. If you would like to
00:19:39.960 subscribe, because I'm also in the
00:19:41.280 process of trying to work out what the
00:19:42.720 best strategy is. I found some which are
00:19:44.480 amazing and have been highly profitable,
00:19:46.000 but I think we can always get better by
00:19:47.680 testing more data, and that's what I
00:19:49.480 want to do here on the channel. The goal
00:19:50.880 of today's video was to help you
00:19:52.680 understand what a trading bot is and how
00:19:54.440 to actually set one up the right way,
00:19:56.320 and then in future videos, we'll go in
00:19:58.280 depth on very specific builds and
00:20:00.680 strategies, and do lots of live tests
00:20:02.520 because I'm just still experimenting all
00:20:04.000 the time. I'm even doing a test right
00:20:05.560 now where I've put Claude and GPT and
00:20:07.360 other models up against each other to
00:20:09.440 see which one is the best. So, that is
00:20:11.440 how to build a real trading bot. I'll
00:20:13.720 leave the prompt available below. It's
00:20:15.520 in the WhatsApp community on the pinned
00:20:17.360 link. And of course, if you want to keep
00:20:18.960 leveling up your own trading and
00:20:20.360 investing, subscribe to the channel as
00:20:22.560 I'll be bringing you the AI strategies
00:20:24.560 that can help you stay at the forefront
00:20:26.720 and [music] the edge of the market. I'll
00:20:28.520 see you in the next video. Have a lovely
00:20:30.240 rest of your day. Peace out.

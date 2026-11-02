
# tactiq.io free youtube transcript

# AI Trading Bot on Windows: Live Demo with Python, Streamlit & Interactive Brokers

# https://www.youtube.com/watch/tLlQHMzFXCs

00:00:00.240 Hello everybody. This is going to be a
00:00:01.520 big long well I don't want to say long
00:00:03.439 video but it'll be an important video to
00:00:05.600 watch. Uh okay. So uh today's July 11,
00:00:09.760 2025.
00:00:11.679 Couple things here to mention. Gro 4
00:00:14.000 just came out. Uh all I can say is the
00:00:16.960 claims of being the best LLM out there
00:00:19.840 model. Uh a bunch of lies. I've
00:00:23.039 experimented with it all day for code
00:00:25.039 generation, for stock analysis, for text
00:00:28.320 generation. and it's still nowhere as
00:00:29.920 close as either to the Gemini 2.5 Pro or
00:00:34.160 the uh Claw 3.7 Reasoning. Nowhere
00:00:37.520 close. Um but it's fast and it's low
00:00:41.520 cost. I'll give it that. But the quality
00:00:43.120 outputs nowhere as good. Um anyways, so
00:00:46.719 I've got here stock analysis uh word uh
00:00:50.000 document. I posted this in my analytics
00:00:52.480 for those that have access to it. Um in
00:00:55.520 here what's the important part is I've
00:00:57.760 prompted it to give for each stock or
00:01:00.640 ETF the entry point the exit uh as well
00:01:05.199 and the stop loss. So the AI does all
00:01:07.200 that as I've shown before. So we're now
00:01:09.680 using that. Couple things to take note
00:01:11.840 here that's important. I have tried to
00:01:14.560 run. You can see here I have my TWWS at
00:01:18.479 the bottom there. That little uh
00:01:20.560 interactive brokers creator workstation
00:01:23.759 is open. This is probably the most
00:01:25.680 important part of the whole video. Um if
00:01:27.920 you're trying to run a Python script to
00:01:30.240 connect into the Windows
00:01:32.640 uh hosted TWWs,
00:01:35.040 it won't run because it's not
00:01:36.320 connecting. um you either have to use uh
00:01:39.600 the WSL IP address to feed it into the
00:01:43.840 TWWS on the Windows host uh and allow it
00:01:47.520 that way or if you're trying to do all
00:01:48.880 local host it won't run. So all your
00:01:50.960 Python scripting has to be local in your
00:01:54.079 Windows host environment, not in the
00:01:56.079 WSL. So from here on out I have to use
00:01:59.200 WSL.
00:02:00.799 Another takeaway is uh out of all the
00:02:03.680 all the prompting I've done um I have
00:02:07.200 used uh try to use Dash. It's horrible.
00:02:12.560 Really 1980s
00:02:14.959 the prompting for Streamlit's way
00:02:16.959 better. As I said before, more features
00:02:19.360 are added. So I'm sticking with
00:02:22.720 Streamlit. problem is it doesn't work
00:02:25.599 that well on Windows natively and for
00:02:29.280 Python in the way you think it should.
00:02:32.400 So if you're going to run
00:02:35.519 on Windows, you're going to need to use
00:02:37.280 this beast software anaconda. I'm not
00:02:41.280 happy about it. It's about from what I'm
00:02:43.040 seeing maybe 30 gig. It's it's horrible,
00:02:46.400 but this is the only way to do it.
00:02:48.239 That's free though. Uh so you follow the
00:02:50.400 instructions. is I put it in my read me
00:02:52.640 in the script if you got access to this
00:02:54.560 through my Quant Elite programming
00:02:56.720 membership.
00:02:58.560 So this is what you got to read. This is
00:03:00.400 what you got to start with. Okay. So um
00:03:04.480 yeah, you install it. It's fairly simple
00:03:07.519 within the Anaconda software which I got
00:03:10.000 running right there. Um and then all you
00:03:13.120 got to do is create your uh environment.
00:03:16.480 So this one's dedicated to Streamlit.
00:03:19.599 um and you open the terminal. Now, when
00:03:21.840 you install all that, typically when you
00:03:25.040 go into the uh command prompts, you'll
00:03:27.200 see an Anaconda PowerShell prompt, which
00:03:30.560 I'm using right now. Okay, so I have two
00:03:32.959 versions of that. Um let me just close
00:03:36.000 this up.
00:03:38.319 It's confusing. I have too many of
00:03:39.599 these. Now, I'm not using V visual uh VS
00:03:43.120 Code for this. it's much easier, but as
00:03:46.400 I use VS Code, it gets more confusing
00:03:48.159 with multiple projects. So, I just keep
00:03:50.319 with the prompting on the PowerShell or
00:03:52.640 the command prompt and use Sublime. I'm
00:03:55.360 pretty happy with that. My process is
00:03:57.439 much better. All right. So, um yeah, we
00:04:01.040 installed that. Uh I've included in the
00:04:03.599 read me here um all this stuff. Okay,
00:04:07.200 this is to set up um the script that I'm
00:04:10.799 going to show you and it feeds in that
00:04:13.760 extracted data for the trading
00:04:15.519 signaling. Okay, and again that's all
00:04:19.519 this stuff here. So note the uh the
00:04:23.040 article name for today July 11th uh
00:04:27.520 analysis a harsh high sharp ratio
00:04:30.080 identify the most profitable
00:04:32.080 opportunities. So, this is from this
00:04:33.759 point on if you get to this video and
00:04:35.280 you have access to all my memberships
00:04:36.639 here. All right. So, um yeah. So, here's
00:04:40.800 the read me file.
00:04:43.520 Couple things here. I'm going to try to
00:04:46.479 do walk you through this. All right. So,
00:04:50.000 um I'm going to try to break that. No.
00:04:55.680 So, I'll close that out. So in here um
00:04:59.600 there's the it's called sharp trading
00:05:02.000 dashboard as the first uh sharp trading
00:05:06.080 dashboard on Windows. Okay. So and
00:05:08.960 that's Windows 11. You could try to do
00:05:12.080 and run the uh TWWs from Interactive
00:05:15.759 Brokers on Linux.
00:05:18.560 I tried to do that with a variety of
00:05:20.960 options through the uh Interactive
00:05:22.800 Brokers gateway.
00:05:24.800 uh you could try to code generate for
00:05:26.880 Python. It was an utter nightmare for
00:05:29.520 C++.
00:05:31.039 So you could try to do those, but this
00:05:32.720 is an easiest way to get it running. I
00:05:35.680 spent about two days getting to this
00:05:37.039 point to get it running. So I'm showing
00:05:38.400 you what I think is the easiest even
00:05:41.280 though it's not the best or most
00:05:43.199 optimal, but this is the best I can get
00:05:45.600 it. So here um part of it is when you
00:05:49.520 run your stream lit. Okay. Um this is
00:05:53.199 all you got to do. So first thing that
00:05:56.639 this script will do and I it just
00:05:58.400 prompted it this way with the uh claw 37
00:06:02.400 reasoning because it's so advanced and I
00:06:04.880 asked specifically in the prompt don't
00:06:07.199 do anything until you can confirm the
00:06:09.120 connection into uh the PWS. Okay. Very
00:06:14.080 important to understand that this has
00:06:15.440 got to run on your Windows
00:06:18.560 11 uh host not in a WSL uh because it
00:06:23.280 has to directly in the same environment
00:06:25.280 connect into the interactive brokers uh
00:06:28.720 TWWS. Okay. So let's run this.
00:06:34.160 Okay. So there we go. It's going to
00:06:35.440 switch over to the browser now. So it's
00:06:37.680 connecting into the TWWs and I'll guide
00:06:39.919 you through it. uh in this particular
00:06:42.560 version you see here it's successfully
00:06:45.680 using IB in sync it's just I have to say
00:06:50.000 interactive brokers makes it a nightmare
00:06:51.919 trying to get Python working with the
00:06:53.759 TWWS this seems to work it's doing an
00:06:57.280 initial test to get the latest price on
00:06:59.280 Apple
00:07:00.800 uh here's all the data to show you the
00:07:03.759 this is all run locally again on my
00:07:06.000 Windows this Python script is running in
00:07:07.840 my Windows environment as well so you
00:07:10.000 can see here's all the data. Um, and
00:07:12.880 then it checks out that it does connect
00:07:14.800 into the TWWs when it's running. So,
00:07:16.880 make sure that's running as well. Okay.
00:07:19.680 So, now we can launch the dashboard. So,
00:07:22.960 here's the dashboard as it loads up in
00:07:25.199 Streamlit. Um, so here's the uh stocks
00:07:31.199 that came up in that report. I've
00:07:33.360 prompted it in a way where it works
00:07:36.080 well. This is the last sharp ratio. Uh
00:07:39.919 we've got the current price because the
00:07:42.560 markets are closed entry range for the
00:07:45.280 stop uh for the for the entry uh exit
00:07:48.400 the stop loss and the status. So
00:07:50.639 currently as it's connected it's
00:07:53.039 watching. Okay. So here's the projected
00:07:55.919 equity curve for the next four weeks
00:07:58.080 based upon momentum of each stock in a
00:08:02.000 portfolio. Uh I think the portfolio
00:08:04.720 amount could be anything you want. Um,
00:08:07.759 in my case, I'm probably going to do 2
00:08:10.000 to 3,000. I can prompt the AI to come
00:08:13.120 back, say how many shares and all the
00:08:15.199 weight allocation for that as well. Um,
00:08:19.520 so I could do that. Right now, the
00:08:20.879 market's closed. Um, but, uh, the point
00:08:25.360 here is that there's the, uh, projected
00:08:28.240 equity. Um and uh I can I can modify
00:08:33.200 this now to have it running as of uh
00:08:36.399 Monday. And again this is connecting
00:08:38.958 directly into uh interactive brokers. Um
00:08:43.760 I've uploaded some projects to show uh
00:08:47.600 raw Python scripts that will connect
00:08:50.160 into
00:08:51.760 uh into the interactive brokers AWS
00:08:55.200 locally uh to download. I got one uh
00:08:59.279 script that will download market data
00:09:01.519 and another one that will uh do either a
00:09:04.959 buy or sell on a specific stock
00:09:09.120 or ETF with the amount of shares that's
00:09:11.600 passed in the arguments of the prompt of
00:09:13.680 of the Python script. So that's already
00:09:16.160 uploaded to um the group. Actually, I
00:09:20.320 could show that. So, for those that are
00:09:24.000 members or whatnot, um the file share
00:09:28.000 I'm talking about here, cuz I have three
00:09:29.920 set sets of of the fileshare here.
00:09:33.600 Quantly programming custom files is
00:09:35.600 where you want to go. We have C++. I've
00:09:39.040 upload I've uploaded a boatload of
00:09:41.600 scripts and sample uh C++ programs. So,
00:09:46.320 this could quickly grow if I wanted it
00:09:48.240 to. It's already 30. Uh but anyways,
00:09:51.120 what you're looking for is the
00:09:52.720 interactive brokers stocks
00:09:55.839 examples. And in there there's the two
00:09:58.959 um examples of it said. So in here we've
00:10:02.320 got um let's see here. It should load
00:10:05.600 up.
00:10:09.120 Okay. So yeah. So if you go into the
00:10:11.760 folder here, you can see here there's
00:10:13.920 the downloader, the stock order for the
00:10:16.160 buy and sell, and the read me as well.
00:10:20.399 So that's that. But this is only
00:10:22.160 available for my Quant Leap members. You
00:10:24.480 got to ask about it and and formally ask
00:10:27.040 me about if you want access. It's not
00:10:28.959 cheap. I had a big sale on it last week.
00:10:31.440 But anyways, um so there's that. So now
00:10:35.040 I'm going to upload the same script to
00:10:36.880 the same folder on my fileshare for the
00:10:39.760 elite members so they get it. Uh it will
00:10:42.399 include the readme and the source code
00:10:44.800 file to get this running. So, um,
00:10:49.360 we are close to getting the trading
00:10:51.760 running. I've got this running as well,
00:10:54.320 the stock selection, but I'm actually
00:10:55.839 going to make it a generic version of
00:10:58.079 this in Python um with a CSV which will
00:11:01.839 have these
00:11:03.680 associated columns like the last sharp
00:11:06.480 ratio, the current price, the entry uh
00:11:10.240 range, exit target, the stop loss for
00:11:14.240 well the downside and also the weight
00:11:18.240 allocation percentwise
00:11:20.959 and a dollar wise depending upon uh the
00:11:23.920 portfolio you want. So you can run it
00:11:27.200 and customize it for any
00:11:29.760 any uh portfolio you use through the CSV
00:11:33.920 with the appropriate um the appropriate
00:11:38.399 uh uh data in the CSV. Also, um what
00:11:43.200 this will do is it will uh connect into
00:11:46.720 Interactive Brokers. It will do the live
00:11:48.800 trading. As you can see, it's kind of
00:11:50.000 ready to go, but I'll probably update
00:11:51.360 this next week. And then, um, it will
00:11:54.720 watch and trade using just a simple
00:11:58.399 current price
00:12:00.320 and, uh, and just do an entry price, um,
00:12:03.440 and then monitor it, um, through your
00:12:07.360 TWWs or, your interactive brokers uh,
00:12:11.200 um, app. And there's not a lot of
00:12:14.079 sophistication to it. This is not meant
00:12:15.760 to be a sophisticated Python script. Uh
00:12:19.360 so if if it hits the current price, uh
00:12:22.880 it'll exit the trade. Now I'm trying to
00:12:25.440 do this every day, every week. Um but I
00:12:29.040 have to put some more intelligence into
00:12:30.480 the script. So I'll update that script
00:12:33.120 as time passes to build in the logic. So
00:12:35.760 for example, if uh you run these uh
00:12:40.959 >> data connection loss
00:12:42.320 >> these um stocks or ETFs
00:12:46.079 and then let's say one of these drops
00:12:49.680 off for whatever reason they said sell
00:12:52.399 it if it's not profitable and I can add
00:12:54.720 that logic in or uh if it's a new stock
00:12:58.480 let's say Robin Hood comes on on here
00:13:00.240 again uh it'll add that um and then the
00:13:04.399 other problem is you got to make sure
00:13:05.519 you have enough funding in the account
00:13:07.839 for the new orders. So, um I'll have to
00:13:11.279 put in a better position in there and
00:13:13.680 it's going to be one generic script. It
00:13:16.000 will not be very sophisticated on
00:13:17.920 purpose. Um but I'm going to build that
00:13:20.399 out. Um and again here, it's not as
00:13:24.720 featurerich as we call it uh as a past
00:13:28.079 simul.
00:13:31.040 Um, but you know, it's it's good enough
00:13:34.399 and uh everything's the same as I've
00:13:37.519 shown before. The only difference now
00:13:39.680 runs in
00:13:42.240 uh Windows. The script will run directly
00:13:44.959 in Windows as I said with the Anaconda
00:13:47.920 running cuz the virtual environment is
00:13:49.360 much easier to run. I mean, like I said,
00:13:50.720 it's a 30 gig piece. I don't know what
00:13:52.560 they'll tell you about that. And uh it's
00:13:56.240 streamllet which is still the number one
00:13:58.720 dashboard front end I've seen in Python
00:14:00.959 not dash but streamlet's the best for
00:14:03.600 open source unless you want to go with
00:14:05.040 commercial one but I think streamlin is
00:14:07.120 really good but when you pass in some of
00:14:09.040 the prompting as I said in the past you
00:14:12.079 will get updated um features you didn't
00:14:15.519 ask for as part of the code and new
00:14:18.320 features that are part of within streams
00:14:20.880 which is pretty mind-blowing what I've
00:14:22.720 shown before. So as this gets updated,
00:14:25.360 I'm going to at some point make it as
00:14:27.040 generic as possible. So you're going to
00:14:28.480 add in new uh CSVs
00:14:32.560 uh common separated value files as time
00:14:36.880 passes and at the same time date trading
00:14:39.199 logic in it so that if there's positions
00:14:42.240 that are profitable leave them and then
00:14:44.480 add in
00:14:46.800 uh stocks and ETFs as time passes and if
00:14:50.160 market conditions allow but um you know
00:14:53.519 it's it's pretty basic uh from what I've
00:14:56.560 been running for the last two weeks on
00:14:58.160 the equity TF and stock these still
00:15:01.839 continually continuously still the best
00:15:04.880 performing
00:15:06.480 uh stocks even if there's a bit of a
00:15:08.160 downside in the market in the last
00:15:10.160 couple of days but um yeah it's getting
00:15:13.360 there and it as far as I know it direct
00:15:15.519 as of today directly connects as you can
00:15:18.000 see you're connected to interactive
00:15:19.760 brokers so it's doing that and then once
00:15:22.320 you get more sophisticated you can um
00:15:24.800 autoexecute the trades as well So,
00:15:27.839 pretty good features. Um, and I'll keep
00:15:30.160 that available in my members the elite
00:15:33.040 only. All right, we'll talk to you soon.
00:15:34.800 Thank you.

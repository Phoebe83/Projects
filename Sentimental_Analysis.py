#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 16:45:43 2018

@author: yuehan
"""

#This programming applied sentimental analysis for news, draw the wordcloud 
#based on the sentimental analysis, calculated the average compound score for 
#each company each day and draw chart based on it, and putting the chart together
#with the history stock price chart for comparison. 

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud,STOPWORDS
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
import plotly
import plotly.plotly as py
import plotly.graph_objs as go

plotly.tools.set_credentials_file(username='Phoebe64', api_key='3j3zsGP8FBJTXwvgLQG5')


#Define a funtion to conduct sentimental analysis.
#The analysis consists of four columns from the sentiment scoring: Neu, Neg, Pos and compound. 
#The 'neu', 'neg' and 'pos' represent the sentiment score percentage of each category 
#in our headline, and the compound single number that scores the sentiment. 
#'compound' ranges from -1 (Extremely Negative) to 1 (Extremely Positive).
def sentimental_analysis(newsDf, attribute):    
    sia = SIA()
    analysis = []
    
    text = newsDf[attribute]
    for line in text:
        pol_score = sia.polarity_scores(str(line))
        pol_score[attribute] = line
        analysis.append(pol_score)
    
    #Save the result into a dataframe
    pol_result = pd.DataFrame.from_records(analysis)
    pol_result['date'] = newsDf['publication_date'].str.split('T', 0).str[0]
    pol_result['ticker'] = newsDf['ticker']
    
    #Define posts with a compound value greater than 0.2 as positive (1)
    #and less than -0.2 as negative (-1); otherwise, netural (0).
    polarity = []
    for i in pol_result['compound']:
        if i > 0.2:
            polarity.append(1)
        elif i < -0.2:
            polarity.append(-1)
        else:
            polarity.append(0)

    pol_result['polarity'] = pd.DataFrame(np.array(polarity))
    return pol_result

#Define a function to create histogram for polarity
def pol_hist(summary_pol): 
    x = summary_pol['polarity']
    trace = go.Histogram(
        x = x,
        marker = dict(color = ' #ffa64d', opacity = 0.85)
    )
    data = [trace]
    layout = go.Layout(
        title = 'Sentimental Analysis of News, News Polarity',
        xaxis = dict(title = 'Polarity',
                     ticktext=['Negative', 'Neutral', 'Positive'],
                     tickvals = [-1, 0 ,1]),
        yaxis = dict(title = 'Frequency'),
        bargap = 0.3
    )
    fig = go.Figure(data=data, layout=layout)
    py.iplot(fig, filename = 'polarity histogram')
    
#Define a function to draw the wordcloud
def wordcloud_draw(data, color = 'black'):
    words = ' '.join(data)
    cleaned_word = " ".join([word for word in words.split()
                            if 'http' not in word
                                and not word.startswith('@')
                                and not word.startswith('#')
                                and word != 'RT'
                            ])
    wordcloud = WordCloud(stopwords=STOPWORDS,
                      background_color=color,
                      width=2500,
                      height=2000
                     ).generate(cleaned_word)
    plt.figure(1,figsize=(13, 13))
    plt.imshow(wordcloud)
    plt.axis('off')
    plt.show()

# Draw the wordcloud for each company based on their titles.
# For each company, draw a white wordcloud for its positive news titles,
# and draw a black wordcloud for its negative titles.  
def title_wordcloud(title_pol):
    tickers = title_pol.ticker.unique().tolist()
    
    for i in range(0,len(tickers)):
        t=title_pol.loc[title_pol.ticker==tickers[i]] #select the ticker
        
        pos_news = []
        neg_news = []
        for index, row in t.iterrows(): 
            if (row['compound'] > 0):
                pos_news.append(row['title'])
            elif (row['compound'] < 0):
                neg_news.append(row['title'])
        
        #draw word cloud
        print("Positive news for compamy " + tickers[i])
        wordcloud_draw(pos_news,'white')
        print("Negative news for compamy " + tickers[i])
        wordcloud_draw(neg_news,'black')
    
#Define a function to get the average compound score in the sentimental analysis
#for each company each day
def compound_mean(summary_pol):
    tickers = summary_pol.ticker.unique().tolist()
    
    d_cmeanT=pd.DataFrame() #Create a dataframe for compound mean
    for i in range(0,len(tickers)):
        t=summary_pol.loc[summary_pol.ticker==tickers[i]] #select the ticker
        ds=t.date.unique().tolist() #put the dates in the tickers to a list
        means = [] #calculate means and write to this list
        for d in ds:
            cs=t.loc[t.date==d]
            means.append(cs["compound"].mean())
    
        #Change lists to dataframes
        ds=pd.DataFrame(ds)
        means=pd.DataFrame(means)
        ticker_name=pd.DataFrame([tickers[i]]*len(ds))
        #merge togather to a new frame
        d_cmean=pd.merge(ds, means, left_index=True, right_index = True)
        d_cmean=pd.merge(d_cmean, ticker_name, left_index=True, right_index = True)
        d_cmean.columns=['date','compound_mean', 'ticker']
        d_cmeanT = pd.concat([d_cmeanT,d_cmean])
    
    return d_cmeanT

#Define a function to merge the compound score dataframe with the dataframe
#created in project 2
def merge(myDf, d_cmeanT):
    result = pd.merge(myDf, d_cmeanT, on=['ticker','date'], how='outer', sort = True)
    return result

#Define a function to draw the stock price history chart and sentimental
#analysis score history for each company 
def draw_graph(result, marketDf):
    tickers = result.ticker.unique().tolist()[:10]
    
    for i in range(0,len(tickers)):  
        company=marketDf.loc[marketDf.ticker==tickers[i]]    
        trace1 = go.Candlestick(x=company['date'],
                           open=company['adj open'],
                           high=company['adj high'],
                           low=company['adj low'],
                           close=company['adj close'],
                           name='Stock Price Trend')
        
        ticker = result.loc[result.ticker == tickers[i]]
        trace2 = go.Bar(x = ticker['date'],
                   y = ticker['compound_mean'],
                   yaxis = 'y2',
                   marker = dict(color = 'rgb(128,128,128)',
                                opacity = 0.5),
                   name = 'Sentimental Score')
        data = [trace1, trace2]
        
        ticker_str = tickers[i]
        layout = go.Layout(
            title = 'The Stock Price for Company ' + ticker_str + ' 9/28/2017- 9/27/2018',
            yaxis = dict(title = 'Stock Price'),
            yaxis2 = dict(title = 'Sentimental Score', 
                          overlaying = 'y',
                          side='right',
                          range=[-.5,3]
                         )
            )     
        fig = dict(data=data, layout=layout)
        py.iplot(fig, filename='Candlestick for Company' + ticker_str)
        
        
if __name__ == '__main__':
    #Import the news data as newsDf, and MergeredData from project 2 as myDf
    #and CleanedMarketData as marketDf. 
    newsDf = pd.read_csv("newsDF.csv", encoding='utf-8')
    newsDf.drop_duplicates('title', inplace=True) #drop duplicated news
    newsDf = newsDf.reset_index(drop=True) #reset the index
    myDf = pd.read_csv("MergeredData.csv")
    marketDf = pd.read_csv("CleanedMarketData.csv")
    
    #Apply sentimental analysis to the title of each news
    title_pol = sentimental_analysis(newsDf, 'title')
    # Apply sentimental analysis to the summary of each news
    summary_pol = sentimental_analysis(newsDf, 'summary')
    #write out to a csv file summary_pol.csv
    summary_pol.to_csv("summary_pol.csv", index= False)
    #Draw histogram for polarity
    pol_hist(summary_pol)
    #Draw positive and negative title wordcloud for each company.
    title_wordcloud(title_pol)
    #Get the average compound score for each company each day
    comp_mean = compound_mean(summary_pol)
    #Merge the compound mean with the dataframe created in Project 2
    result = merge(myDf, comp_mean)
    ##write out the result to a csv file summary_pol.csv
    result.to_csv("Sentimental_score.csv", index= False)
    #draw the stock price history chart and sentimental
    #analysis score history for each company
    draw_graph(result, marketDf)
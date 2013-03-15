# -*- coding: utf-8 -*-
'''
MetMast
-------

A straightforward met mast import class built with the pandas library

'''
from __future__ import print_function
from __future__ import division
import os
import json
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as spystats
import header_classifier as hclass
import weibull_est as west

class MetMast(object): 
    '''Subclass of the pandas dataframe built to import and quickly analyze
       met mast data.'''
       
    def __init__(self, lat=None, lon=None, height=None, time_zone=None):
        '''Data structure with both relevant information about the mast
        itself (coordinates, height, time zone), as well as methods to process
        the met mast data and manipulate it using tools from the pandas
        library. 
        
        Parameters
        ----------
        lat: float, default None
            Latitude of met mast
        long: float, default None
            Longitude of met mast
        height: float or int, default None
            Height of met mast
        time_zone: string
            Please follow the pytz time zone conventions: 
            http://pytz.sourceforge.net/
        '''
        self.lat = lat
        self.lon = lon
        self.height = height
        self.time_zone = time_zone
        
    def wind_import(self, path, columns=None, header_row=None, time_col=None,
                    delimiter=',', smart_headers=True, **kwargs):
        '''Wind data import. This is a very thin wrapper on the pandas read_table 
        method, with the option to pass keyword arguments to pandas read_table 
        if needed. 
    
        Parameters:
        ----------
        path: string
            Path to file to be read
        header_row: int
            Row containing columns headers
        time_col: int
            Column with the timestamps
        delimiter: string, default=','
            File delimiter
        smart_headers: boolean, default True
            Uses NLTK text classifier to predict column headers
    
        Returns: 
        --------
        DataFrame with wind data
        '''
        
        if time_col is None:
            raise ValueError('Please enter a value for time_col')
        
        print('Importing data...')
        self.data = pd.read_table(path, header=header_row, index_col=time_col, 
                                  parse_dates=True, delimiter=delimiter,
                                  **kwargs)
                                  
        if smart_headers:                       
            '''Smart parse columns for Parameters'''
            data_columns = self.data.columns.tolist()
            data_columns = [x.strip().lower() for x in data_columns]
            
            #Import NLTK classifier (see header_classifier.py)
            pkg_dir, filename = os.path.split(__file__)
            classifier_path = os.path.join(pkg_dir, 'classifier.pickle')
            with open(classifier_path, 'r') as f: 
                classifier = pickle.load(f)   
                     
            #Search dict for parameter match, rename column
            iter_dict = {'Wind Speed StDev': 1, 
                         'Wind Speed': 1, 
                         'Wind Direction': 1, 
                         'TI':1}
            new_columns = []
            for x, cols in enumerate(data_columns): 
                get_col = classifier.classify(hclass.features(cols))
                new_col = '{0} {1}'.format(get_col, str(iter_dict[get_col]))
                new_columns.append(new_col)
                iter_dict[get_col] += 1
            self.data.columns = new_columns
            print(('The following column headers have been generated by ' 
                   'smart_headers:\n'))
            col_print = [x+' --> '+y for x,y in zip(data_columns, 
                                                    new_columns)]
            for x in col_print:
                print(x)
                                       
    def weibull(self, column=None, ws_intervals=1, method='LeastSq', 
                plot=None):
        '''Calculate distribution and weibull parameters
        
        Parameters:
        ___________
        column: string
            Column to perform weibull analysis on
        ws_intervals: float, default=1
            Wind Speed intervals on which to bin
        method: string, default 'LeastSq'
            Weibull calculation method. 
        plot: string, default None
            Choose whether or not to plot your data, and what method. 
            Currently only supporting matplotlib, but hoping to add 
            Bokeh as that library evolves. 
            
        Returns: 
        ________
        DataFrame with hourly data distributions
        '''
        
        ws_range = np.arange(0,self.data[column].max()+ws_intervals, 
                             ws_intervals)
        binned = pd.cut(self.data[column], ws_range)
        dist_10min = pd.value_counts(binned).reindex(binned.levels)
        dist = pd.DataFrame({'Binned: 10Min': dist_10min})
        dist['Binned: Hourly'] = dist['Binned: 10Min']/6
        dist = dist.fillna(0)
        normed = dist['Binned: 10Min']/dist['Binned: 10Min'].sum()
        data = normed.values
        x = np.arange(0, len(data), ws_intervals)
        
        if method == 'LeastSq':
            A,k = west.least_sq(data,x)
            A = round(A, 3)
            k = round(k, 3)
            rv = spystats.exponweib(1, k, scale=A, floc=0)
            
        if plot == 'matplotlib':
            fig, ax1 = plt.subplots()
            ax1.bar(x, dist['Binned: Hourly'], color='#A70043')
            ax1.set_xlabel(r'Wind Speed [m/s]')
            ax1.set_ylabel(r'Hours')
            ax2 = ax1.twinx()
            smooth = np.arange(0, len(data), 0.1)
            ax2.plot(smooth, rv.pdf(smooth), color='#61B100', linewidth=2.0)
            ax2.set_ylabel(r'PDF')
            
            
        return {'Weibull A': A, 'Weibull k': k, 'Dist': dist}
            
    def sectorwise(self, sectors=12, **kwargs):
        '''Bin the wind data sectorwise
        '''
        pass
        if not self.data:
            print(("You have not imported any data. Use the 'wind_import'"
                   "method to load data into your object"))
        cuts = 360/sectors
        bins = [0, cuts/2]
        bins.extend(range(cuts, 360, cuts))
        bins.extend([360-cuts/2, 360])
        cats = pd.cut(self.data['Average Direction'], bins, right=False)
        array = pd.value_counts(cats)
        
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
                                  
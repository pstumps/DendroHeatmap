from math import pi
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import dendrogram
from bokeh.plotting import figure, output_notebook, output_file, show
from bokeh.models.sources import ColumnDataSource
from bokeh.models import HoverTool
import argparse
import sys


class DendroHeat:
    '''
    Creates a Bokeh figure of a dendrogram and a heatmap. User only needs to worry about adding data and which figure(s) they want to show.

    instantiation:
        fig = DendroHeat()
    usage:
        fig.addData(file='rawdata.csv', type='raw')
        fig.show(dendrogram=False)
    '''
    
    def __init__ (self):
        '''Create the class with essential components'''
        self.heatmap = ''
        self.linkage = ''
        self.icoord = ''
        self.dcoord = ''
    
    def addData(self, file='', index_col=0, type=''):
        '''Checks if the file exists and what type of data is being added.'''
        if not file:
            raise FileNotFoundError('file does not exist')
        if file.endswith(".xlsx"): df = pd.read_excel(file, index_col=index_col)
        elif file.endswith(".csv"): df = pd.read_csv(file, index_col=index_col)
        
        if not type:
            raise AssertionError("Please designate datatype - raw or linkage")
        
        if type == "raw":
            self.heatmap = df

        if type == "linkage":
            self.linkage = df
            dendro = dendrogram(self.linkage, no_plot=True)
            self.icoord, self.dcoord = dendro['icoord'], dendro['dcoord']
            self.heatmap = self.heatmap.iloc[dendro['ivl']]

    def _createHeatmap (self, tool=True):
        '''Create the Heatmap from the raw data. Color intensity of cells are based on the normalization of each column'''
        if self.heatmap is None:
            raise AssertionError("No raw data added - cannot make heatmap")
        df = self.heatmap
        ndf = (df - df.min(axis=0)) / (df.max(axis=0) - df.min(axis=0))

        name = []
        attribute = []
        crange = ['#66ff66', '#00ffff', '#000099', '#6600ff', '#ff00ff', '#990099', '#ff0066', '#993333', '#ff9933', '#ffff00']
        colors = []
        xs = []
        ys = []
        alpha = []
        value = []

        for i, m in enumerate(df.index):
            name = name + [m]*len(df.columns)
            attribute = attribute + df.columns.tolist()
            colors = colors + crange*2
            xs = xs + list(np.arange(0.5, len(df.columns)+0.5))
            ys = ys + [i+0.5]*len(df.columns)
            value = value + df.loc[m].tolist()
            alpha = alpha + ndf.loc[m].tolist()

        self.data = dict(name = name, attribute = attribute, colors = colors, xs = xs, ys = ys, value = value, alpha = alpha)
        self.source = ColumnDataSource(self.data)

        # Currently text is floating outside of the figure on the x axis.
        # Need to add it to the bottom of the heatmap so x_range can become bigger w/o messing with labels.
        hm = figure(x_range=self.heatmap.columns.tolist(), y_range=[0, self.heatmap.shape[0]])

        # Creates hover tool from heatmap data
        if tool:
            hover = HoverTool(names=['Heatmap'])
            hover.tooltips = [("Name", "@name"), ("Attribute", "@attribute"), ("Value", "@value")]
            hm.add_tools(hover)
        
        hm.rect(x='xs', y='ys', height=1, width=1, source=self.source, fill_alpha='alpha', line_alpha=0.1, name='Heatmap', fill_color='colors')

        # Some housekeeping to clean heatmap axes and labels
        hm.xaxis.major_label_orientation = pi/2
        hm.xaxis.major_label_text_font_size = '7pt'
        hm.axis.major_tick_line_color = None
        hm.axis.minor_tick_line_color = None
        hm.yaxis.major_label_text_color = None
        hm.grid.grid_line_color = None
        hm.axis.axis_line_color = None
        self.heatmap = hm
    
    def _createDendrogram(self):
        '''
        Creates dendrogram based off of the i coordinates and d coordinates provided by scipy's dendrogram dictionary. 
        Uses bokeh to create lines on the heatmap based off of the values of these coordinates.
        '''
        if self.linkage is None:
            raise AssertionError("No linkage data added - cannot make dendrogram")
        self.icoord = pd.DataFrame(self.icoord)
        self.dcoord = pd.DataFrame(self.dcoord)
        self.icoord = self.icoord*(max(self.data['ys'])/self.icoord.max().max())
        self.dcoord = self.dcoord*(max(self.data['xs'])/self.dcoord.max().max())
        ycoord = self.icoord.values
        xcoord = self.dcoord.values

        for i, d in zip(ycoord, xcoord):
            d = list(map(lambda x: -x, d))
            self.heatmap.line(x=d, y=i,  line_width = 0.2, line_color = 'black', name='Dendrogram')

    def show(self, output='html', heatmap=True, dendrogram=True):
        '''Outputs the Heatmap and Dendrogram'''

        # create figures based on user input
        if heatmap:
            self._createHeatmap()
        if dendrogram:
            self._createDendrogram()

        # configure output file
        if output == 'notebook':
            output_notebook()
        elif output == 'html':
            if heatmap and dendrogram:
                output_file("dendroheat.html", "Heatmap with Dendrogram")
            elif heatmap:
                output_file("heatmap.html", "Heatmap")
        
        show(self.heatmap)

class CommandLine(): 
    '''
    Handle the command line, usage and help requests.
    CommandLine uses argparse, now standard in 2.7 and beyond.
    it implements a standard command line argument parser with various
    argument options, a standard usage and help.
    attributes:
    all arguments received from the commandline using .add_argument will be
    avalable within the .args attribute of object instantiated from CommandLine.
    For example, if myCommandLine is an object of the class, and requiredbool was
    set as an option using add_argument, then myCommandLine.args.requiredbool will
    name that option.
    '''
    def __init__(self, inOpts) : 
        '''
        Implement a parser to interpret the command line argv string using argparse.
        '''

        self.parser = argparse.ArgumentParser(description = 'Produces a heatmap with or without a dendrogram. This program will accept raw data and an associated linkage matrix in the form of an excel or csv file and visualize both using Bokeh.',
                                            epilog = 'Note: Program cannot run with only the linkage matrix',
                                            add_help = True,
                                            usage = '%(prog)s heatmapFile linkageFile')
        self.parser.add_argument('raw', action = 'store', help='Heatmap data file')
        self.parser.add_argument('linkage', action = 'store', nargs='?', default='', help='Provide linkage matrix for dendrogram creation.')
        self.parser.add_argument('-v, --version', action='version', version='%(prog)s 0.3')
        self.args = self.parser.parse_args(inOpts)
        
def main(inCL = None): 
    argsParse = CommandLine(inCL)
    raw = argsParse.args.raw
    linkage = argsParse.args.linkage

    dh = DendroHeat()
    dh.addData(file=raw, type='raw')
    if linkage: dh.addData(file=linkage, type='linkage')
    dh.show()
    

if __name__ == "__main__": main()
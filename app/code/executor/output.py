import os
import dominate
from dominate.tags import *

def generateOutput(outputfile, output):

    doc = dominate.document(title='Results')

    with doc:
        h1('Results')
        hr()
        for result in output:
            h2(result['ROI'])
            with table():
                with tbody():
                    with tr():
                        with td(rowspan=6):
                            h3('Globals')
                        global_labels = result['global_stats']['covariate_labels']
                        global_labels.insert(0,'') 
                        for i in global_labels:
                            td(i)
                    with tr():
                        global_coefficient = result['global_stats']['Coefficient']
                        global_coefficient.insert(0,'Coefficient')
                        for i in global_coefficient:
                            td(i)
                    with tr():
                        global_tstat = result['global_stats']['t Stat']
                        global_tstat.insert(0,'t Stat')
                        for i in global_tstat:
                            td(i)
                    with tr():
                        global_pvalue = result['global_stats']['P-value']
                        global_pvalue.insert(0,'P-value')
                        for i in global_pvalue:
                            td(i)
                    with tr():
                        global_rsquared = result['global_stats']['R Squared']
                        td('R Squared')
                        td(global_rsquared, colspan=5)
                    with tr():
                        global_degfree = result['global_stats']['Degrees of Freedom']
                        td('Degrees of Freedom')
                        td(global_degfree, colspan=5)
                for site in result['local_stats']:
                    with tbody():
                        with tr():
                            with td(rowspan=6):
                                h3(site)
                            global_labels = result['global_stats']['covariate_labels']
                            for j in global_labels:
                                td(j)
                        with tr():
                            local_coefficient = result['local_stats'][site]['Coefficient']
                            local_coefficient.insert(0,'Coefficient')
                            for i in local_coefficient:
                                td(i)
                        with tr():
                            local_tstat = result['local_stats'][site]['t Stat']
                            local_tstat.insert(0,'t Stat')
                            for i in local_tstat:
                                td(i)
                        with tr():
                            local_pvalue = result['local_stats'][site]['P-value']
                            local_pvalue.insert(0,'P-value')
                            for i in local_pvalue:
                                td(i)
                        with tr():
                            local_errors = result['local_stats'][site]['Sum Square of Errors']
                            td('Sum Square of Errors')
                            td(local_errors, colspan=5)
                        with tr():
                            local_rsquared = result['local_stats'][site]['R Squared']
                            td('R Squared')
                            td(local_rsquared, colspan=5)

    with open(outputfile, "a") as f:
        print(doc, file=f)

        print('<style>', file=f)

        styles = '''
            body {
                font-family: sans-serif;
            }
            hr {
                width: 100%;
            }
            table {
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 0.9em;
                font-family: sans-serif;
                min-width: 400px;
                width: 100%;
            }
            table thead tr {
                background-color: #009879;
                color: #ffffff;
                text-align: left;
            }
            table tr:nth-of-type(1) td {
                font-weight: bold;              
            }
            table tr td:nth-of-type(1) {
                background-color: white;
                font-weight: bold;
            }
            table tr td[colspan]{
                background-color: white;
            }
            table thead tr td { 
                text-transform: capitalize;
            }
            table th,
            table td {
                padding: 12px 15px;
                white-space: nowrap;
            }
            table tbody tr {
                border-bottom: 1px solid #dddddd;
            }
            
            table tbody tr:nth-of-type(even) {
                background-color: #efefef;
            }
            
            table tbody tr.active-row {
                font-weight: bold;
                color: #009879;
            }
        '''
        print(styles, file=f)
        print('</style>', file=f)

import csv
import xml.etree.ElementTree as ET
import re
import networkx as nx
import matplotlib.pyplot as plt
from collections import namedtuple
G=nx.DiGraph()
Main_list = []
fields = ['Request_Method','URL','Host','Referer','Origin','CSRF_Token','Form','sensitive_parameters','status_code','content_type',
         'outgoing_URL','Server','x_frame_options','x_xss','content_length','comments']
Request = namedtuple('Request', fields)
def CDATA(text=None):
    element = ET.Element('![CDATA[')
    element.text = text
    return element


def parseXML(xmlfile):
    # create element tree object
    tree = ET.parse(xmlfile)

    # get root element
    root = tree.getroot()

    # create empty list for news items
    data = []

    for item in root.findall('.//Request'):

        # empty news dictionary
        request = {}
        ownPath = ""
        # iterate child elements of item
        for child in item:
            request[child.tag] = child.text
            if child.tag == "RequestHeader":
                request_method = getReqMethod(child.text)
                host = getHost(child.text)
                URL = getURL(request_method, child.text)
                referer = getReferer(child.text)
                origin = getOrigin(child.text)
                G.add_node(URL)
                if referer!=None:
                    G.add_node(referer)
                    G.add_edge(referer,URL)
            if child.tag == "ResponseData":
                getHref(URL,child.text)
            if child.tag == "ResponseHeader":
                status_code = getStatusCode(child.text)
                content_type = getContentType(child.text)

            # special checking for namespace object content:media

        # append news dictionary to news items list
        data.append(request)
       # Main_list.append(Request(Request_Method,URL,Host,Referer,Origin,CSRF_Token,Form,sensitive_parameters,status_code,content_type,
        # outgoing_URL,Server,x_frame_options,x_xss,content_length,comments))

        # return news items list
    nx.draw(G, with_labels=True)
    plt.show()
    return data


### XML to python..................................
def savetoCSV(requestitems, filename):
    # specifying the fields for csv file
    fields = ['HostName', 'Port', 'SSL', 'URL', 'RequestHeader', 'RequestData', 'ResponseHeader', 'ResponseData']

    # writing to csv file
    with open(filename, 'w') as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames=fields)

        # writing headers (field names)
        writer.writeheader()

        # writing data rows
        writer.writerows(requestitems)

### links through href....................
def getHref(ownPath,childPath):
    href = re.findall(r'href=\"[^<]*\"', childPath)
    for link in href:
        if link[6]=="/":
            path = link[6:-1]
        else:
            path = "/"+link[6:-1]
        G.add_node(path)
        G.add_edge(ownPath,path)
    print("NODES:")
    print(G.nodes())
    print("EDGES:")
    print(G.edges())
    #D = G.to_directed()

### own url.......................................
def getURL(method,child):
    method_length = len(method)
    url = re.findall(r'.*HTTP/1.1', child)
    ownPath = re.sub('[\s+]', '', url[0])
    return ownPath[method_length:-8]

### referer........................................
def getReferer(child):
    hostname = re.findall(r'Host\:.*', child)
    hostname = hostname[0]
    hostname = hostname[6:]
    referer = re.findall(r'Referer: http://', child)
    if len(referer)==0:
        return None
    referer = referer[0]+ hostname
    refererString = (re.findall(r'Referer: http://.*',child))
    refererString = refererString[0]
    return refererString[len(referer):]

###pagerank.........................................
def pagerank(G, alpha=0.85, personalization=None,
             max_iter=5, tol=1.0e-2, nstart=None, weight='weight',
             dangling=None):

    if len(G) == 0:
        return {}

    if not G.is_directed():
        D = G.to_directed()
    else:
        D = G

        # Create a copy in (right) stochastic form
    W = nx.stochastic_graph(D, weight=weight)
    N = W.number_of_nodes()

    # Choose fixed starting vector if not given
    if nstart is None:
        x = dict.fromkeys(W, 1.0 / N)
    else:
        # Normalized nstart vector
        s = float(sum(nstart.values()))
        x = dict((k, v / s) for k, v in nstart.items())

    if personalization is None:

        # Assign uniform personalization vector if not given
        p = dict.fromkeys(W, 1.0 / N)
    else:
        missing = set(G) - set(personalization)
        if missing:
            raise NetworkXError('Personalization dictionary '
                                'must have a value for every node. '
                                'Missing nodes %s' % missing)
        s = float(sum(personalization.values()))
        p = dict((k, v / s) for k, v in personalization.items())

    if dangling is None:

        # Use personalization vector if dangling vector not specified
        dangling_weights = p
    else:
        missing = set(G) - set(dangling)
        if missing:
            raise NetworkXError('Dangling node dictionary '
                                'must have a value for every node. '
                                'Missing nodes %s' % missing)
        s = float(sum(dangling.values()))
        dangling_weights = dict((k, v / s) for k, v in dangling.items())
    dangling_nodes = [n for n in W if W.out_degree(n, weight=weight) == 0.0]

    # power iteration: make up to max_iter iterations
    for i in range(max_iter):
        xlast = x
        x = dict.fromkeys(xlast.keys(), 0)
        danglesum = alpha * sum(xlast[n] for n in dangling_nodes)
        for n in x:

            # this matrix multiply looks odd because it is
            # doing a left multiply x^T=xlast^T*W
            for nbr in W[n]:
                x[nbr] += alpha * xlast[n] * W[n][nbr][weight]
            x[n] += danglesum * dangling_weights[n] + (1.0 - alpha) * p[n]

        # check convergence, l1 norm
        err = sum([abs(x[n] - xlast[n]) for n in x])
        if err < N * tol:
            return x

    raise nx.NetworkXError('pagerank: power iteration failed to converge '
                        'in %d iterations.' % max_iter)

##hostname:
def getHost(child):
    hostname = re.findall(r'Host\:.*', child)
    hostname = hostname[0]
    hostname = hostname[6:]
    print(hostname)

###request method................
def getReqMethod(child):
    method = re.findall(r'.*HTTP/1.1', child)
    method = method[0]
    method = re.findall(r'[^/]*', method)
    method = re.sub('[\s+]', '', method[0])
    return method

##Origin..........................
def getOrigin(child):
    origin = re.findall(r'Origin.*', child)
    if len(origin)!=0:
        origin = re.sub('[\s+]', '', origin[0])
        print(origin[7:])
        return origin[7:]
    else:
        return None

def getCsrfToken(child):

#--------------RESPONSE ...............
###status code.....................
def getStatusCode(child):
    status = re.findall(r'HTTP.*', child)
    status = re.sub('[\s+]', '', status[0])
    print(status[8:11])
    return status[8:11]

#content type.........................
def getContentType(child):
    contentType = re.findall(r'Content-Type.*',child)
    if len(contentType)!=0:
        contentType = re.sub('[\s+]', '', contentType[0])
        return (contentType[13:])
    else:
        return None

def main():

    # parse xml file
    requestitems = parseXML('test123.xml')

    # store news items in a csv file
    #savetoCSV(requestitems, 'myrequests.csv')
    #p = pagerank(G, alpha=0.85, personalization=None,
        #     max_iter=5, tol=1.0e-6, nstart=None, weight='weight',
         #    dangling=None)
    #print(p)

if __name__ == "__main__":
    # calling main function
    main()
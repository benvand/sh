from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from forms import PostcodeForm, LLForm
import json
import config
from geopy.point import Point
from geopy import geocoders, distance
import requests


class DistanceMixin():
    """Mixin with methods for extracting information from the headers and json
    and using this information to calculate distance
    """
    geocoder = config.geocoder or geocoders.GoogleV3()
    destination = config.destination

    def getDistance(self, (olat, olng), (dlat, dlng)):
        """
        Great Circle Distance of 2 points on globe
        indicated by longitude and latitude arguments
        Args:
            tuple(olat, olng) -
                olat = origin latitude, str
                olng = origin longitude, str
            tuple(dlat, dlng) -
                dlat = destination latitude, str
                dlng = destination longitude, str
        """
        return str(distance.GreatCircleDistance(
            Point(olat, olng),
            Point(dlat, dlng)).kilometers)

    def getIP(self, request):
        """
        Extracts IP from request headers
        Prefers 'HTTP_X_FORWARDED_FOR' will accept 'REMOTE_ADDR'
        Args:
            request - request object
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def getJSONElement(self, request, element):
        """Grabs element from request json dict
        Args:
            request - request object
            element - str dictionary key
        """
        return json.loads(request.body)[element]

    def fromPostcode(self, pcode, destination):
        """
        Given pcode as origin geocodes pcode as postcode
        returns distance to destination
        Args:
            pcode - str origin postcode
            destination - tuple(lat, lng) destination lat and long
        """
        place, (lat, lng) = self.geocoder.geocode(pcode)
        distance = self.getDistance((lat, lng), destination)
        return distance

    def fromLatLong(self, (lat, lng), destination):
        """
        Wrapper for self.getDistance to keep with convention
        (fromPostcode, fromLatLong, fromIP)
        Args:
            (lat, lng) - tuple(originlatitude, originlongitude)
            destination - - tuple(destlatitude, destlongitude)
        """
        distance = self.getDistance((lat, lng), destination)
        return distance

    def fromIP(self, ip, destination):
        """
        Requests location from freegeoip api
        uses location as origin
        returns distance from dest
        Args:
            ip - str
            destination- tuple(destlatitude, destlongitude)
        """
        response = requests.get('http://freegeoip.net/json/%s' % ip).json()
        lat, lng = response['latitude'], response['longitude']
        distance = self.getDistance((lat, lng), destination)
        return distance

    def fdist(self, distance):
        """
        format distance returned to json
        Args:
            distance - str
        """
        ele = {'distance': str(distance) + 'km'}
        return json.dumps(ele)

    def fhelp(self, apihelp):
        """
        format help returned to json
        Args:
            apihelp - str
        """
        ele = {'help': apihelp}
        return ele


#Class based views

class Distance(View, DistanceMixin):
    """

    """
    def get(self, request, *args, **kwargs):
        """
        First get of page will produce a guess of location from IP
        Takes IP from header with getIP from DistanceMixin
        """
        ip = self.getIP(request)
        ipDist = self.fromIP(ip, config.destination)
        return render(request, 'distance/distance.html',
                      {'ip': ip, 'ipDist': ipDist, "LLForm": LLForm,
                       'PostcodeForm': PostcodeForm})

    def post(self, request, *args, **kwargs):
        ip = self.getIP(request)
        ipDist = self.fromIP(ip, config.destination)
        # Very basic try excepts to return none from queryobject if not key
        try:
            pcode = request.POST['postcode']
        #Below handles instance of None returned from form (ie. clicking
        #with nothing in the input. Should be handled in form validator )
            if pcode:
                pcode = pcode.upper()
                pcodeDist = self.fromPostcode(pcode, config.destination)
            else:
                pcodeDist = None
        except KeyError:
            pcode = pcodeDist = None
        #Not the same here as we can just return None from self.fromLatLong
        try:
            lat = request.POST['latitude']
            lng = request.POST['longitude']
            llDist = self.fromLatLong((lat, lng), config.destination)
        except KeyError:
            lng = lat = llDist = None
        #Pack it all up into dict to be passed as context
        context = {'ip': ip,
                   'ipDist': ipDist,
                   'LLForm': LLForm,
                   'PostcodeForm': PostcodeForm,
                   'lat': lat,
                   'lng': lng,
                   'llDist': llDist,
                   'pcode': pcode,
                   'pcodeDist': pcodeDist}
        return render(request, 'distance/distance.html', context)



class BaseApiView(View, DistanceMixin):
    apiHelp = ""

    def get(self, request, *args, **kwargs):
        """
        Basic help get view
        If not overridden will attempt to return self.apiHelp as json
        """
        return HttpResponse(json.dumps((self.fhelp(self.apiHelp))))



class Api(BaseApiView):
    apiHelp = \
    """
    This api shows you the distance to Sharehood!

    The methods are

    GET
        http://myserver/distance/api/pc
            Help text for the corresponding POST function
        http://myserver/distance/api/ll
            Help text for the corresponding POST function
        http://myserver/distance/api/ip
            Distance from your current IP
    POST
        http://myserver/distance/api/pc
            CONTEXT should be json in format {'postcode':'se6 1sx'}
        http://myserver/distance/api/ll
            CONTEXT should be json in format {"latitude":"123.456789",
                                              "longitude":"123.456789"}
        http://myserver/distance/api/ip
            CONTEXT should be json in format {'ip':'192.168.1.1'}

    To get you started why not open a python prompt and try some of these:
    import requests, json

    requests.post("servername/distance/api/pc",
        (json.dumps({"postcode":"SW1A 2AA"})).json()

    requests.get("servername/distance/api/ip").json()

    requests.post("servername/distance/api/pc",
        (json.dumps({"latitude":"25.0000", "longitude":"71.0000"})).json()
    """




class ApiIP(BaseApiView):
    """
    Override get return the requesters IP here
    URL http://myserver/distance/api/ip

    GET
    Response:  {u'distance': u'5730.63058749km'}

    POST
    CONTEXT json.dumps({'ip':'86.129.25.251'})
    Response {u'distance': u'3470.02077216km'}
    """
    def get(self, request, *args, **kwargs):
        ip = self.getIP(request)
        return HttpResponse(self.fdist(self.fromIP(ip, config.destination)))

    def post(self, request, *args, **kwargs):
        ip = self.getJSONElement(request, 'ip')
        return HttpResponse(
            self.fdist(self.fromPostcode(ip, config.destination)))

class ApiPostcode(BaseApiView):
    apiHelp = \
    """
    URL http://myserver/distance/api/pc

    GET
    Response:  {u'help': <this help text>}

    POST
    CONTEXT json.dumps({'postcode':'se6 1sx'})
    Response {u'distance': u'11.6605825103km'}
    """

    def post(self, request, *args, **kwargs):
        pc = self.getJSONElement(request, 'postcode')
        return HttpResponse(
            self.fdist(self.fromPostcode(pc, config.destination)))


class ApiLatLong(BaseApiView):
    apiHelp = \
    """
    URL /distance/api/ll

    GET
    Response:  {u'help': <this help text>}

    POST
    CONTEXT json.dumps({"latitude":"123.456789", "longitude":"123.456789"})
    Response {u'distance': u'16398.8129049km'}
    """

    def post(self, request, *args, **kwargs):
        lat = self.getJSONElement(request, 'latitude')
        lng = self.getJSONElement(request, 'longitude')
        return HttpResponse(self.fdist(
            self.fromLatLong((lat, lng), config.destination)
        ))
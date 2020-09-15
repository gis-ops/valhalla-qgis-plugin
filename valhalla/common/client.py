# -*- coding: utf-8 -*-
"""
/***************************************************************************
                                 Valhalla - QGIS plugin
 QGIS client to query Valhalla APIs
                              -------------------
        begin                : 2019-10-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Nils Nolde
        email                : nils@gis-ops.com
 ***************************************************************************/

 This plugin provides access to the various APIs from OpenRouteService
 (https://openrouteservice.org), developed and
 maintained by GIScience team at University of Heidelberg, Germany. By using
 this plugin you agree to the ORS terms of service
 (https://openrouteservice.org/terms-of-service/).

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from datetime import datetime, timedelta
import requests
import time
from urllib.parse import urlencode
import random
import json

from qgis.PyQt.QtCore import QObject, pyqtSignal, QUrl, QJsonDocument
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import QgsNetworkAccessManager, QgsNetworkReplyContent

from valhalla import __version__
from valhalla.common import networkaccessmanager
from valhalla.utils import exceptions, logger

_USER_AGENT = "ValhallaQGISClient@v{}".format(__version__)


class Client(QObject):
    """Performs requests to the ORS API services."""

    def __init__(self,
                 provider=None,
                 retry_timeout=60):
        """
        :param provider: A openrouteservice provider from config.yml
        :type provider: dict

        :param retry_timeout: Timeout across multiple retriable requests, in
            seconds.
        :type retry_timeout: int
        """
        QObject.__init__(self)

        self.key = provider['key']
        self.base_url = provider['base_url']
        
        # self.session = requests.Session()
        self.nam = QgsNetworkAccessManager()

        self.retry_timeout = timedelta(seconds=retry_timeout)
        self.headers = {
                "User-Agent": _USER_AGENT,
                'Content-type': 'application/json',
            }

        # Save some references to retrieve in client instances
        self.url = None
        self.warnings = None
        self.response_time = 0
        self.status_code = None

    overQueryLimit = pyqtSignal()
    def request(self, 
                url,
                first_request_time=None,
                retry_counter=0,
                post_json=None):
        """Performs HTTP GET/POST with credentials, returning the body as
        JSON.

        :param url: URL extension for request. Should begin with a slash.
        :type url: string

        :param first_request_time: The time of the first request (None if no
            retries have occurred).
        :type first_request_time: datetime.datetime

        :param post_json: Parameters for POST endpoints
        :type post_json: dict

        :raises valhalla.utils.exceptions.ApiError: when the API returns an error.

        :returns: openrouteservice response body
        :rtype: dict
        """

        if not first_request_time:
            first_request_time = datetime.now()

        elapsed = datetime.now() - first_request_time
        if elapsed > self.retry_timeout:
            raise exceptions.Timeout()

        if retry_counter > 0:
            # 0.5 * (1.5 ^ i) is an increased sleep time of 1.5x per iteration,
            # starting at 0.5s when retry_counter=1. The first retry will occur
            # at 1, so subtract that first.
            delay_seconds = 1.5**(retry_counter - 1)

            # Jitter this value by 50% and pause.
            time.sleep(delay_seconds * (random.random() + 0.5))

        # Define the request
        params = {'access_token': self.key}
        authed_url = self._generate_auth_url(url,
                                             params,
                                             )
        url_object = QUrl(self.base_url + authed_url)
        self.url = url_object.url()
        body = QJsonDocument.fromJson(json.dumps(post_json).encode())
        request = QNetworkRequest(url_object)
        request.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')

        logger.log(
            "url: {}\nParameters: {}".format(
                self.url,
                # final_requests_kwargs
                json.dumps(post_json, indent=2)
            ),
            0
        )

        start = time.time()
        response: QgsNetworkReplyContent = self.nam.blockingPost(request, body.toJson())
        self.response_time = time.time() - start

        try:
            self.handle_response(response, post_json['id'])
        except exceptions.OverQueryLimit:
            # Let the instances know smth happened
            self.overQueryLimit.emit()
            return self.request(url, first_request_time, retry_counter + 1, post_json)

        response_content = json.loads(bytes(response.content()))

        # Mapbox treats 400 errors with a 200 status code
        if 'error' in response_content:
            raise exceptions.ApiError(
                str(response_content['status_code']),
                response_content['error']
            )

        return response_content

    def handle_response(self, response, feat_id):
        """
        Casts JSON response to dict

        :raises valhalla.utils.exceptions.OverQueryLimitError: when rate limit is exhausted, HTTP 429
        :raises valhalla.utils.exceptions.ApiError: when the backend API throws an error, HTTP 400
        :raises valhalla.utils.exceptions.InvalidKey: when API key is invalid (or quota is exceeded), HTTP 403
        :raises valhalla.utils.exceptions.GenericServerError: all other HTTP errors

        :returns: response body
        :rtype: dict
        """

        self.status_code = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if response.error():
            # First try non-HTTP error codes
            error_code = response.error()
            error_msg = response.errorString()
            if error_code in (QNetworkReply.ConnectionRefusedError, QNetworkReply.HostNotFoundError):
                raise exceptions.GenericServerError(1, f"Host {self.base_url} not valid.")
            elif error_code == QNetworkReply.TimeoutError:
                raise exceptions.Timeout("Request timed out.")

            print(self.status_code)
            if self.status_code == 401:
                raise exceptions.InvalidKey(
                    str(self.status_code),
                    error_msg
                )
            elif self.status_code == 429:
                logger.log("{}: {}".format(
                    exceptions.OverQueryLimit.__name__,
                    "Query limit exceeded"
                ))
                raise exceptions.OverQueryLimit(
                    str(429),
                    error_msg
                )
            # Internal error message for Bad Request
            elif self.status_code and 400 <= self.status_code < 500:
                logger.log("Feature ID {} caused a {}: {}".format(
                    feat_id,
                    exceptions.ApiError.__name__,
                    error_msg,
                    2
                ))
                raise exceptions.ApiError(
                    str(self.status_code),
                    error_msg
                )
            else:
                raise exceptions.GenericServerError(
                    str(self.status_code),
                    error_msg
                )

    def _generate_auth_url(self, path, params):
        """Returns the path and query string portion of the request URL, first
        adding any necessary parameters.

        :param path: The path portion of the URL.
        :type path: string

        :param params: URL parameters.
        :type params: dict or list of key/value tuples

        :returns: encoded URL
        :rtype: string
        """
        
        if type(params) is dict:
            params = sorted(dict(**params).items())
        
        # Only auto-add API key when using ORS. If own instance, API key must
        # be explicitly added to params
        # if self.key:
        #     params.append(("api_key", self.key))

        return path + "?" + requests.utils.unquote_unreserved(urlencode(params))

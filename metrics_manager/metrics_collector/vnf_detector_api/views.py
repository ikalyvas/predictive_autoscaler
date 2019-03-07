# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import requests

# Create your views here.
from django.conf import settings
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from .serializers import VnfSerializer


# Create your views here.


class VnfViewSet(viewsets.GenericViewSet):


    vnf_elk_url = 'http://'+settings.ELASTICSEARCH['HOST']+settings.ELASTICSEARCH['port']+'/'+settings.ELASTICSEARCH['vnf_index']+'/_doc/{vnf_id}'

    def get_serializer_class(self):
        if self.action == 'create':
            return VnfSerializer

    def create(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vnf_id = serializer.data['vnf_identifier']
        vdur = serializer.data['vdur']
        r = requests.post(self.vnf_elk_url.format(vnf_id=vnf_id), data={'vdur':vdur})


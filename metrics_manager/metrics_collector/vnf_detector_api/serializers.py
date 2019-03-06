from rest_framework import serializers


class VnfSerializer(serializers.Serializer):

    """
        Looks like the following


              { "vnf_identifier": "7a8861c8-e66a-4a85-9d30-24368e62c721",
                "vdur": [
                        {
                            "interfaces": [
                                {
                                    "ip-address": "192.168.107.5",
                                    "mac-address": "fa:16:3e:34:16:21",
                                    "name": "eth0"
                                }
                            ],
                            "ip-address": "192.168.107.5",
                            "name": "ns_auto-2-autoscale_cirros_vnfd-VM-1",
                            "status": "ACTIVE",
                            "status-detailed": "null",
                            "vdu-id-ref": "cirros_vnfd-VM",
                            "vim-id": "3cff32c0-c208-4f6d-9e8a-84a49f113e13"
                        },
                        {
                            "interfaces": [
                                {
                                    "ip-address": "192.168.107.16",
                                    "mac-address": "fa:16:3e:1b:e2:e6",
                                    "name": "eth0"
                                }
                            ],
                            "ip-address": "192.168.107.16",
                            "name": "ns_auto-2-autoscale_cirros_vnfd-VM-2",
                            "status": "ACTIVE",
                            "status-detailed": "null",
                            "vdu-id-ref": "cirros_vnfd-VM",
                            "vim-id": "6b6af824-38c7-491b-abdb-a5cfdf0f9cdd"
                        }
                    ]
                }
            ]
            }


    """


    vnf_identifier = serializers.CharField(max_length=100)
    vdur = serializers.ListField()
#!/bin/bash
#Copyright 2023, Battelle Energy Alliance, LLC
urls="google.com:443"
for url in $urls; do
openssl s_client -showcerts -verify 5 -connect $url < /dev/null |
   awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/{ if(/BEGIN CERTIFICATE/){a++}; out="cert"a".pem"; print >out}'
for cert in *.pem; do
        newname=$(openssl x509 -noout -subject -in $cert | sed -nE 's/.*CN ?= ?(.*)/\1/; s/[ ,.*]/_/g; s/__/_/g; s/_-_/-/; s/^_//g;p' | tr '[:upper:]' '[:lower:]').pem
        echo "${newname}"; mv "${cert}" "${newname}" || true
done
done
sudo cp ca*root.pem /usr/local/share/ca-certificates/caroot.crt || true
sudo  update-ca-certificates


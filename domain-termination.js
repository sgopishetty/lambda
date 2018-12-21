'use strict';
var AWS = require("aws-sdk");
var route53 = new AWS.Route53();
var Domain;
var instance_ip;
var session_id;
var jibri_domain;
var jibriip;
exports.handler = (event, context, callback) => {
    // TODO implement
    
    session_id = event.sessionId;
    console.log("Session Id:", session_id);
    
    Domain = event.sessionId+".edvie.com";
    console.log('Domain:', event.sessionId+".edvie.com");
    
    instance_ip = event.instanceip;
    console.log('jitsipublicip:', instance_ip);
    
    jibri_domain = "recorder_"+event.sessionId+".edvie.com";
    console.log('Jibri_Domain:', "recorder_"+event.sessionId+".edvie.com");
    
    jibriip = event.jibriinstanceip;
    console.log('Jibri Public Ip:', event.jibriinstanceip);
    
    if (event.jibriinstanceip == "") {
      removeRoute53Record(event.instanceip, event.sessionId);
      const response1 = {
        statusCode: 200,
        body: JSON.stringify({"status": "Remove Route53 Record successful", "JitsiDomain": Domain}),
    };
     callback(null, response1);
    }
    else {
      removeRoute53Record(event.instanceip, event.sessionId);
      removejibriRecord(event.jibriinstanceip, event.sessionId);
    }
    const response = {
        statusCode: 200,
        body: JSON.stringify({"status": "Remove Route53 Record successful", "JitsiDomain": Domain, "JibriDomain": jibri_domain}),
    };
       callback(null, response);
}; 



function removeRoute53Record(event, instanceip, sessionId){
    var hostedZoneId = "Z2S8NDZVRP07VL";
    var params = {
        ChangeBatch: { 
            Changes: [ 
      {
        Action: 'DELETE', 
        ResourceRecordSet: { 
          Name: Domain, 
          Type: 'A',
          TTL: 300,
          ResourceRecords: [
            {
              Value: instance_ip
            }
          ]
        }
      },
    ],
    Comment: 'OS'
  },
  HostedZoneId: hostedZoneId
};

route53.changeResourceRecordSets(params, function(err, data) {
      if (err) {
      console.log(err, err.stack);
        }
        else {
            console.log("Remove Jitsi DNS record successful from route53" + data);
        }
    });
}

function removejibriRecord(event, jibriinstanceip, sessionId){
    var hostedZoneId = "Z2S8NDZVRP07VL";
    var params2 = {
        ChangeBatch: { 
            Changes: [ 
      {
        Action: 'DELETE', 
        ResourceRecordSet: { 
          Name: jibri_domain, 
          Type: 'A',
          TTL: 300,
          ResourceRecords: [
            {
              Value: jibriip
            }
          ]
        }
      },
    ],
    Comment: 'OSE'
  },
  HostedZoneId: hostedZoneId
};

route53.changeResourceRecordSets(params2, function(err, data) {
      if (err) {
      console.log(err, err.stack);
        }
        else {
            console.log("Remove Jibri DNS record successful from route53" + data);
        }
    });
}

var AWS = require("aws-sdk");
var route53 = new AWS.Route53();
var ec2 = new AWS.EC2();
var session_id;
var instance_id;
var Domain;
var instance_ip;
var jibri_instance_id;
var jibri_instance_ip;
var jibri_domain;

exports.handler = function(event, context , callback) {
    
    // TODO implement
    session_id = event.sessionId;
    console.log('Session Id:', event.sessionId);
    
    instance_id = event.instanceId;
    console.log('Instance Id:', event.instanceId);
    
    jibri_instance_id = event.jibriinstanceid;
    console.log('Jibri_Instance_Id:', event.jibriinstanceid);
    
    Domain = event.sessionId+".edvie.com";
    console.log('Domain:', event.sessionId+".edvie.com");
    
    jibri_domain = "recorder_"+event.sessionId+".edvie.com";
    console.log('Jibri_Domain:', "recorder_"+event.sessionId+".edvie.com");
    
    if ( event.jibriinstanceid == "null") {
        ec2.waitFor("instanceRunning", {InstanceIds: [instance_id]}, function(err, data) {
        if (err) return console.error(err);
        
        instance_ip = data.Reservations[0].Instances[0].PublicIpAddress;
        console.log('JitsiPublicIp: ' + data.Reservations[0].Instances[0].PublicIpAddress);
        console.log('JitsiPublicIp:' + instance_ip);
        
    removeRoute53Record(event.instanceId, event.sessionId);
    cloudWatchEventRemove(event.sessionId);
    
    });
    terminateInstance(event.instanceId,event.jibriinstanceid);
    const response1 = {
       statusCode: 200,
        body: JSON.stringify({"status":"Instance temination Successful","session":event.sessionId})
    };
    
    callback(null, response1);
    
    }
    else {
    
        ec2.waitFor("instanceRunning", {InstanceIds: [instance_id,jibri_instance_id]}, function(err, data) {
        if (err) return console.error(err);
        
        instance_ip = data.Reservations[0].Instances[0].PublicIpAddress;
        jibri_instance_ip = data.Reservations[0].Instances[0].PublicIpAddress;
        console.log('JitsiPublicIp: ' + data.Reservations[0].Instances[0].PublicIpAddress);
        console.log('JitsiPublicIp:' + instance_ip);
        console.log('JibriPublicIp:' + data.Reservations[0].Instances[0].PublicIpAddress);
        console.log('JibriInstanceIp'+ jibri_instance_ip);
        
        removeRoute53Record(event.instanceId, event.sessionId);
        removejibriRecord(event.jibriinstanceid, event.sessionId);
        cloudWatchEventRemove(event.sessionId);
        
        });
        terminateInstance(event.instanceId,event.jibriinstanceid);
        const response = {
        statusCode: 200,
            body: JSON.stringify({"status":"Instance temination Successful","session":event.sessionId, "jibri_domain":jibri_domain})
        };
        callback(null, response);
    }
};
    
    


function cloudWatchEventRemove(event, sessionId){
    //var ruleName = event.sessionId;
    //console.log('ruleName ::::', ruleName);
    var cloudwatchevents = new AWS.CloudWatchEvents();
    var params = {
        Name: session_id
    };
    var paramsTarget = {
        "Rule" : params.Name,
        "Ids" : ['sessionId']
};

cloudwatchevents.removeTargets(paramsTarget, function(err, data) {
    if (err) {
      console.log(err, err.stack);
    } else {
        console.log(data);
        
cloudwatchevents.deleteRule(params, function(err, data) {
    if (err) {
        console.log(err, err.stack);
    } else {
        console.log("Delete cloudwatch rule successful! - data: " + JSON.stringify(data, null, 2));
    }
      });
    }
  });
}

function removeRoute53Record(event, instanceId, sessionId){
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
    Comment: 'OSE'
  },
  HostedZoneId: hostedZoneId
};

route53.changeResourceRecordSets(params, function(err, data) {
      if (err) {
      console.log(err, err.stack);
        }
        else {
            console.log("Remove jitsi DNS record successful from route53" + data);
        }
    });
}

function removejibriRecord(event, jibri_instance_id, sessionId){
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
              Value: jibri_instance_ip,
            }
          ]
        }
      },
    ],
    Comment: 'OS'
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

function terminateInstance(event, instanceId, jibriinstanceid){
     console.log("instanceId ::::"+instance_id+"::::"+jibri_instance_id);
    var params;
    if(jibri_instance_id != '' && jibri_instance_id != 'null'){
         params = {InstanceIds: [instance_id,jibri_instance_id]};
    }else{
         params = {InstanceIds: [instance_id]};
    }
    console.log("Params ::::"+JSON.stringify(params));
ec2.terminateInstances(params, function(e, data) {
    if (e)
        console.log(e, e.stack);
    else
        console.log("Terminate instance successful!" + data);
});
}
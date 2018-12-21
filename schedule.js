var AWS = require("aws-sdk");
var lambda = new AWS.Lambda;

exports.handler = function(event, context , callback) {
    // TODO implement
    console.log('Session Id:', event.sessionId);
    console.log('Cron Expression:', event.cronExp);
    console.log('Recording:', event.recording);
    
    cloudWatchEventSchedule(event.sessionId,event.cronExp,event.recording);
    
    const response = {
       statusCode: 200,
        body: JSON.stringify({"session":event.sessionId})
    };
    callback(null, response); 
};


function cloudWatchEventSchedule(sessionId,cronExp,recording){
    var cloudwatchevents = new AWS.CloudWatchEvents();
    var scheduleExpression = "cron("+ cronExp +")";
    //var scheduleExpression = "cron(09 02 * * ? *)";
    //var scheduleExpression = "2018-10-10T01:22:00Z";
    var params = {
        Name: sessionId,
        ScheduleExpression: scheduleExpression,
        State: 'ENABLED',
    };
    cloudwatchevents.putRule(params, function(err, data) {
        if (err) {
            console.log(err, err.stack);  
        }
        else {
            console.log(data);
    var lambdaparams = {
        Action: "lambda:InvokeFunction",
        FunctionName: "jitsi-create-liveclass",
        Principal: "events.amazonaws.com",
        StatementId: sessionId
    };
    lambda.addPermission(lambdaparams, function(err, data) {
   if (err) console.log(err, err.stack); // an error occurred
   else     console.log(data); 
    });
    var targetParams = {
        Rule : params.Name,
        Targets : [
            {
              Id : 'sessionId',
              Arn : 'arn:aws:lambda:us-west-2::function:jitsi-create-liveclass',
              //RoleArn: params['RoleArn'],
              Input : JSON.stringify({sessionId: sessionId,schedule:'true',recording: recording}),
              //Input : JSON.stringify({sessionId: 123})
            }
        ]
    };
    cloudwatchevents.putTargets(targetParams, function(err, data) {
        if (err) {
            console.log(err, err.stack);  
        }
        else {
            console.log("Created a event"+ data);
        }
    });
    }
});
}

This ASP.NET Framework 4.x code uses to translate posted data by graylog HTTP Notification and submit to Twillio SMS API.
You will need these information from your Twillio account:
- MessagingServiceSid from Messaging Service (Develop -> Messaging -> Services)
- AccountSid from your project
- AuthToken from your project

```
<%@ Page Language="C#" AutoEventWireup="true" %>
<%@ Import Namespace="System.Net" %>
<%@ Import Namespace="System.Collections" %>
<%@ Import Namespace="System.Text.RegularExpressions" %>
<script runat="server">
protected void Page_Load(object sender, EventArgs e) {

	System.Net.ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls | SecurityProtocolType.Tls11 | SecurityProtocolType.Tls12;

	var stream = new System.IO.StreamReader(HttpContext.Current.Request.InputStream);
	var jsonText = stream.ReadToEnd();
	
	if (String.IsNullOrEmpty(jsonText)) 
		return;
		
	var m = Regex.Match(jsonText, @"event_definition_title"":""([^""]+)");
	var bodyText = m.Groups[1].Value;
	
	if (String.IsNullOrEmpty(bodyText)) 
		return;
	
	Send("+12345678900", bodyText);
	System.Threading.Thread.Sleep(1000);
	Send("+12345678901", bodyText);
}

private void Send(string number, string bodyText) {
	var MessagingServiceSid = "MG56...";
	var AccountSid = "AC3432...";
	var AuthToken = "90af1...";
	var Url = "https://api.twilio.com/2010-04-01/Accounts/" + AccountSid + "/Messages.json";

	var values = new NameValueCollection();
	
	values.Add("To", number);
	values.Add("MessagingServiceSid", MessagingServiceSid);
	values.Add("Body", bodyText);
	
	using (var client = new WebClient()) {
		client.Headers.Add("Content-Type", "application/x-www-form-urlencoded");
		client.Credentials = new NetworkCredential(AccountSid, AuthToken);
		byte[] result = client.UploadValues(Url, "POST", values);
		var resultText = System.Text.Encoding.UTF8.GetString(result);
		Response.Write(resultText);
	}
}
</script>
```

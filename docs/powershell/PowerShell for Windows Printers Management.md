# PowerShell for Windows Printers Management
This code snippet tested with PowerShell 7, you can download it here: https://github.com/PowerShell/PowerShell/releases/tag/v7.1.4

## Enable PowerShell Remoting (optional)
To manage printers on a remote computer, enable PowerShell Remoting on the remote computer:

```powershell
Enable-PSRemoting -Force
Set-Item wsman:\localhost\client\trustedhosts *
Restart-Service WinRM
```

Connect to the remote computer using a username and password. This credential must be created on the remote computer.

```powershell
$PSSessionConfigurationName = 'PowerShell.7'
$User = 'Administrator'
$Pass = 'myPassword'
$PassSecured = ConvertTo-SecureString -AsPlainText $Pass -Force
$Cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PassSecured
Enter-PSSession -ComputerName COMPUTER_NAME -Credential $Cred
```

OK, now you are connected to the remote computer, any command with be run on it.

## Get Printers

```powershell
Get-Printer | Where Name -Like "EPSON*" | Select Name, PortName
```

## Get Printer Ports with IP Address

```powershell
Get-PrinterPort | Where Name -Like 'EPSON*' | Select-Object -Property Name, PrinterHostAddress
```

## Add a Printer Port which using LPR protocol

```powershell
Add-PrinterPort -Name "EPSON_PORT_P9500_1" -LprHostAddress "192.168.10.26" -LprQueueName "_"
```

## Add a Printer

```powershell
Add-Printer -Name "EPSON P9500 - 1" -DriverName "EPSON SC-P9500 Series" -PortName "EPSON_PORT_P9500_1"
```

## Remove a Printer

```powershell
Remove-Printer -Name "EPSON P9500 - 1"
```

To remove a printer, make the printer queue does not have any pending print job.

## Remove a Printer Port

```powershell
Remove-PrinterPort -Name "EPSON_PORT_P9500_1"
```

## List Print Jobs

```powershell
Get-PrintJob -PrinterName "EPSON P9500 - 1" | Select Id, DocumentName, SubmittedTime, JobStatus
```
You will see a list of print jobs with Id. You will need these Ids to remove (cancel) print jobs.

```
 Id DocumentName                                      SubmittedTime        JobStatus
 -- ------------                                      -------------        ---------
114 filename                                          5/27/2021 3:29:57 PM      8210
129 filename                                          5/27/2021 3:29:57 PM         0
```

## Remove a Print Job

```powershell
Remove-PrintJob -PrinterName "EPSON P9500 - 1" -Id 114
```


#include "LogCapture.h"
UPythonLogCaptureContext::UPythonLogCaptureContext()
{
	Capture = MakeShared<FPythonLogCapture>().ToSharedPtr();
}
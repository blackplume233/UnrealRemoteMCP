#pragma once
#include "LogCapture.generated.h"

DECLARE_DYNAMIC_DELEGATE_OneParam(FPythonLogCaptureDelegate,FString,Log);

class ILogCapture
{
public:
	virtual void ProcessLog(const FString& Log) = 0;
	virtual ~ILogCapture(){};
};

class FLogCaptureDevice : public FOutputDevice
{
public:
	virtual void Serialize(const TCHAR* V, ELogVerbosity::Type Verbosity, const FName& Category) override
	{
		FString Msg = FString::Printf(TEXT("[%s] %s \n"), *Category.ToString(), V);
		for (auto Record : Records)
		{
			if (Record.IsValid())
				Record.Pin()->ProcessLog(Msg);
		}
		
	}

	FLogCaptureDevice()
	{
		if (GLog)
			GLog->AddOutputDevice(this);
	}

	virtual ~FLogCaptureDevice() override
	{
		if (GLog)
			GLog->RemoveOutputDevice(this);
	}

	inline static void AddCapture(const TSharedPtr<ILogCapture>& Capture)
	{
		if (Device == nullptr)
		{
			Device = MakeShared<FLogCaptureDevice>();

		}

		Records.Add(Capture);
	}
	inline static void RemoveCapture(const TSharedPtr<ILogCapture>& Capture)
	{
		Records.Remove(Capture);
	}
	
	inline static void RegisterDelegate(const FPythonLogCaptureDelegate& Delegate)
	{
		Delegates.Add(Delegate);
	}
private:
	inline static TSet<TWeakPtr<ILogCapture>> Records;
	inline static TArray<FPythonLogCaptureDelegate> Delegates;
	inline static TSharedPtr<FLogCaptureDevice> Device = nullptr;
};


struct FPythonLogCapture : public ILogCapture
{
	virtual void ProcessLog(const FString& Log) override
	{
		Logs.Add(Log);
	}
	TArray<FString> Logs;
};


UCLASS(BlueprintType)
class  UPythonLogCaptureContext : public UObject
{
	GENERATED_BODY()
	UPythonLogCaptureContext();
public:
	UFUNCTION(BlueprintCallable)
	const TArray<FString>& GetLogs()
	{
		return Capture->Logs;
	}
	
	UFUNCTION(BlueprintCallable)
	void Clear()
	{
		Capture->Logs.Empty();
	}
	
	UFUNCTION(BlueprintCallable)
	void BeginCapture()
	{
		FLogCaptureDevice::AddCapture(Capture);
	}
	
	UFUNCTION(BlueprintCallable)
	void End()
	{
		FLogCaptureDevice::RemoveCapture(Capture);
	}
protected:
	TSharedPtr<FPythonLogCapture> Capture;
};
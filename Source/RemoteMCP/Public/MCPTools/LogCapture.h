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
		if (Records.Num() <= 0 )
			return;
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
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|Log")
	const TArray<FString>& GetLogs(const FString& Name)
	{
		auto Capture = FindOrCreateLogCapture( Name);
		if (Capture.IsValid())
		{
			GLog->FlushThreadedLogs();
			return Capture->Logs;
		}

		return Empty;
	}
	
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|Log")
	void Clear(const FString& Name)
	{
		auto Capture = FindOrCreateLogCapture( Name);
		Capture->Logs.Empty();
	}
	
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|Log")
	void BeginCapture(const FString& Name)
	{
		auto Capture = FindOrCreateLogCapture( Name);
		FLogCaptureDevice::AddCapture(Capture);
	}
	
	UFUNCTION(BlueprintCallable,Category="MCPLibrary|Log")
	void End(const FString& Name)
	{
		auto Capture = FindOrCreateLogCapture( Name);
		FLogCaptureDevice::RemoveCapture(Capture);
	}

	UFUNCTION(BlueprintCallable,Category="MCPLibrary|Log")
	void Delete(const FString& Name)
	{
		auto Capture = FindOrCreateLogCapture( Name);
		FLogCaptureDevice::RemoveCapture(Capture);
		NamedCapture.Remove(Name);
	}

	TSharedPtr<FPythonLogCapture> FindOrCreateLogCapture(const FString& Name)
	{
		if (NamedCapture.Contains(Name))
		{
			return NamedCapture[Name];
		}
		else
		{
			auto NewCapture = MakeShared<FPythonLogCapture>();
			NamedCapture.Add(Name, NewCapture);
			return NewCapture;
		}
	}
protected:
	TMap<FString, TSharedPtr<FPythonLogCapture> > NamedCapture;
	//TSharedPtr<FPythonLogCapture> Capture;
	inline static TArray<FString> Empty;
};
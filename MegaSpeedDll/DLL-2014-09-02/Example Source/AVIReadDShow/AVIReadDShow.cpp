// AVIRead.cpp : Defines the entry point for the console application.
//


#include "stdafx.h"

#include <Windows.h>

#pragma warning(disable: 4995)
#include "dshow.h"
#include "dshow_include\qedit.h"
#include "dshow_include\mtype.h"


#include "DShowHelpers.h"
#include "MS_CameraControl.h"

//Note: Strmbase.lib must be linked here or in the project settings
#pragma comment(lib,"dshow_lib\\Strmbase.lib")

bool ProcessFile(const _TCHAR *Filename);

int _tmain(int argc, _TCHAR* argv[])
{
	// Initialize the COM library.
	HRESULT hr = CoInitialize(NULL);
	if (FAILED(hr))
	{
		printf("ERROR - Could not initialize COM library");
		return 0;
	}

	const _TCHAR *Filename =  L"C:\\ReadExample.avi";

	ProcessFile(Filename);

	CoUninitialize();

	system("Pause");

	return 0;
}



class DShowFrameSource
{
public:
	DShowFrameSource();
	~DShowFrameSource();

	bool OpenFile(const _TCHAR *Filename);
	bool GetFrameData(LONGLONG FrameNum, BYTE* &BufferOut, DWORD &BufferLength);
	void CloseFile();

	inline SIZE GetFrameSize() const	{	if(FileOpen)return FrameSize;	else{ SIZE Empty = {0,0}; return Empty; }	};
	inline LONGLONG GetNumFrames() const {	if(FileOpen)return NumFrames;	else return 0;	};

private:
	void GoToFrameNum(LONGLONG FrameNum);
	void FreeEverything();
	
	bool FileOpen;
	SIZE FrameSize;
	LONGLONG NumFrames;

	IGraphBuilder *pGraph;
	IMediaSeeking *pMediaSeeking;
	IMediaControl *pControl;
	IMediaEventEx *pEvent;
	IBaseFilter *pGrabberF;
	ISampleGrabber *pGrabber;
	IBaseFilter *pSourceF;
	IEnumPins *pEnum;
	IPin *pPin;
	IBaseFilter *pNullF;

	BYTE *pBuffer;
	long cbBuffer;
};

bool ProcessFile(const _TCHAR *Filename)
{
	DShowFrameSource AVIReader;
	bool OpenRes = AVIReader.OpenFile(Filename);
	if(OpenRes == false)
	{
		printf("Error: failed opening the file\n");
		system("Pause");
		return false;
	}

	SIZE FrameSize = AVIReader.GetFrameSize();
	LONGLONG NumFrames = AVIReader.GetNumFrames();
	int ImgWidth = FrameSize.cx;
	int ImgHeight = FrameSize.cy;
	
	if(FrameSize.cy%2 != 1)
	{
		printf("Warning: encoded data line is missing, embedded data is probably absent/corrupt\n");
		system("Pause");
	}

	DWORD FrameSizeBytes;
	BYTE *FrameBuffer;

	char TimestampStr[100] = "";
	char MarkerStr[100] = "";
	int CaptureSpeed=0;
	int ExposureTime=0;

	for(LONGLONG i=0; i<NumFrames; i++)
	{
		bool Result = AVIReader.GetFrameData(i, FrameBuffer, FrameSizeBytes);	//note: buffer and size are passed by ref
		if(Result == false)
		{
			printf("Failed reading frame %d\n", i);
			continue;
		}

		MS_ReadTimeStampFromSavedFrame(FrameBuffer, ImgWidth, ImgHeight-1, false, TimestampStr, 100);
		MS_ReadMarkerFromSavedFrame(FrameBuffer, ImgWidth, ImgHeight-1, MarkerStr, 100);
		CaptureSpeed = MS_ReadCaptureSpeedFromSavedFrame(FrameBuffer, ImgWidth, ImgHeight-1);
		ExposureTime = MS_ReadExposureTimeFromSavedFrame(FrameBuffer, ImgWidth, ImgHeight-1);

		printf("Frame %4d: Marker: %s  Time: %s  FPS: %d  Exp: %d us\n", (int)i, MarkerStr, TimestampStr, CaptureSpeed, ExposureTime);
	}

	return true;
}



DShowFrameSource::DShowFrameSource()
{
	FileOpen = false;

	pGraph = NULL;
	pMediaSeeking = NULL;
	pControl = NULL;
	pEvent = NULL;
	pGrabberF = NULL;
	pGrabber = NULL;
	pSourceF = NULL;
	pEnum = NULL;
	pPin = NULL;
	pNullF = NULL;

	pBuffer = NULL;
}

DShowFrameSource::~DShowFrameSource()
{
	FreeEverything();
}

void DShowFrameSource::CloseFile()
{
	FreeEverything();
}

void DShowFrameSource::FreeEverything()
{
	if(pBuffer != NULL)
		CoTaskMemFree(pBuffer);
	SafeRelease(&pPin);
	SafeRelease(&pEnum);
	SafeRelease(&pNullF);
	SafeRelease(&pSourceF);
	SafeRelease(&pGrabber);
	SafeRelease(&pGrabberF);
	SafeRelease(&pControl);
	SafeRelease(&pEvent);
	SafeRelease(&pMediaSeeking);
	SafeRelease(&pGraph);

	pGraph = NULL;
	pMediaSeeking = NULL;
	pControl = NULL;
	pEvent = NULL;
	pGrabberF = NULL;
	pGrabber = NULL;
	pSourceF = NULL;
	pEnum = NULL;
	pPin = NULL;
	pNullF = NULL;

	pBuffer = NULL;

	FrameSize.cx = 0;
	FrameSize.cy = 0;
	NumFrames = 0;

	FileOpen = false;
}

bool DShowFrameSource::OpenFile(const _TCHAR *Filename)
{
	CloseFile();	//close previously open file if any

	HRESULT hr = CoCreateInstance(CLSID_FilterGraph, NULL, CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&pGraph));
	if(FAILED(hr))
		return false;
	
	HRESULT hr1 = pGraph->QueryInterface(IID_PPV_ARGS(&pControl));
	HRESULT hr2 = pGraph->QueryInterface(IID_PPV_ARGS(&pEvent));
	HRESULT hr3 = pGraph->QueryInterface(IID_PPV_ARGS(&pMediaSeeking));
	if(FAILED(hr1) || FAILED(hr2) || FAILED(hr3))
		return false;

	// Create the Sample Grabber filter.
	hr = CoCreateInstance(CLSID_SampleGrabber, NULL, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&pGrabberF));
	if (FAILED(hr))
		return false;

	hr = pGraph->AddFilter(pGrabberF, L"Sample Grabber");
	if (FAILED(hr))
		return false;

	hr = pGrabberF->QueryInterface(IID_PPV_ARGS(&pGrabber));
	if (FAILED(hr))
		return false;

	AM_MEDIA_TYPE mt;
	ZeroMemory(&mt, sizeof(mt));
	mt.majortype = MEDIATYPE_Video;
	mt.subtype = MEDIASUBTYPE_RGB8;//MEDIASUBTYPE_RGB24;

	hr = pGrabber->SetMediaType(&mt);
	if (FAILED(hr))
		return false;

	hr = pGraph->AddSourceFilter(Filename, L"Source", &pSourceF);
	if(FAILED(hr))
		return false;

	hr = pSourceF->EnumPins(&pEnum);
	if(FAILED(hr))
		return false;

	while (S_OK == pEnum->Next(1, &pPin, NULL))
	{
		hr = ConnectFilters(pGraph, pPin, pGrabberF);
		SafeRelease(&pPin);
		if(SUCCEEDED(hr))
			break;
	}
	if(FAILED(hr))
		return false;

	hr = CoCreateInstance(CLSID_NullRenderer, NULL, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&pNullF));
	if(FAILED(hr))
		return false;

	hr1 = pGraph->AddFilter(pNullF, L"Null Filter");
	hr2 = ConnectFilters(pGraph, pGrabberF, pNullF);
	if(FAILED(hr1) || FAILED(hr2))
		return false;

	hr = pGrabber->SetOneShot(TRUE);
	hr = pGrabber->SetBufferSamples(TRUE);

	hr = pGrabber->GetConnectedMediaType(&mt);
	if(FAILED(hr))
		return false;

	if((mt.formattype == FORMAT_VideoInfo) && (mt.cbFormat >= sizeof(VIDEOINFOHEADER)) && (mt.pbFormat != NULL)) 
	{
		VIDEOINFOHEADER *pVih = (VIDEOINFOHEADER*)mt.pbFormat;
		FrameSize.cx = pVih->bmiHeader.biWidth;
		FrameSize.cy = pVih->bmiHeader.biHeight;
	}
	else 
	{
		// Invalid format.
		hr = VFW_E_INVALIDMEDIATYPE; 
	}

	FreeMediaType(mt);

	hr = pMediaSeeking->SetTimeFormat(&TIME_FORMAT_FRAME);
	hr = pMediaSeeking->GetDuration(&NumFrames);

	if(SUCCEEDED(hr))
		FileOpen = true;

	return SUCCEEDED(hr);
}

void DShowFrameSource::GoToFrameNum(LONGLONG FrameNum)
{
	pMediaSeeking->SetPositions(&FrameNum, AM_SEEKING_AbsolutePositioning, NULL, AM_SEEKING_NoPositioning);
}

bool DShowFrameSource::GetFrameData(LONGLONG FrameNum, BYTE* &BufferOut, DWORD &BufferLength)
{
	GoToFrameNum(FrameNum);

	AM_MEDIA_TYPE mt;
	ZeroMemory(&mt, sizeof(mt));

	HRESULT hr = pControl->Run();

	long evCode;
	hr = pEvent->WaitForCompletion(INFINITE, &evCode);

	if(pBuffer == NULL)	//if buffer hasn't been allocated yet, find the required size and allocate one
	{
		hr = pGrabber->GetCurrentBuffer(&cbBuffer, NULL);
		if(FAILED(hr))
			return false;

		pBuffer = (BYTE*)CoTaskMemAlloc(cbBuffer);
		if(!pBuffer) 
		{
			hr = E_OUTOFMEMORY;
			return false;
		}
	}

	hr = pGrabber->GetCurrentBuffer(&cbBuffer, (long*)pBuffer);
	if(FAILED(hr))
	{
		BufferOut = NULL;
		BufferLength = 0;
		return false;
	}
	else
	{
		BufferOut = pBuffer;
		BufferLength = cbBuffer;
		return true;
	}
}







//new functions:

/////Reads the embedded timestamp from a frame from a previously saved avi, and converts it to a string which is stored in Result
//MS_CAMERACONTROL_API void MS_ReadTimeStampFromSavedFrame(
/////Pointer to the image data the timestamp will be read from
//														 const unsigned char *SrcImg,
/////The width and height of the input frame
/////Note: Height should not include the encoded data row.
//														 int Width, 
//														 int Height, 
/////The timestamp is internally stored as a day in the year (1-365|366) and converted to a month day format
/////The leap year flag will cause February to be treated as either 28 or 29 days long.
//														 bool LeapYear, 
/////The result string is stored here, must not be NULL
//														 char *Result, 
/////Length of the result string buffer
//														 int ResultLength
//														 );
//
/////Reads the embedded marker from a frame from a previously saved avi, and converts it to a string which is stored in Result
//MS_CAMERACONTROL_API void MS_ReadMarkerFromSavedFrame(
/////Pointer to the image data the timestamp will be read from
//														 const unsigned char *SrcImg,
/////The width and height of the input frame
/////Note: Height should not include the encoded data row.
//														 int Width, 
//														 int Height, 
/////The result string is stored here, must not be NULL
//														 char *Result, 
/////Length of the result string buffer
//														 int ResultLength
//													  );
//
/////Reads the embedded capture speed from a frame from a previously saved avi
///// \return The capture speed, in Frames per second
//MS_CAMERACONTROL_API int MS_ReadCaptureSpeedFromSavedFrame(
/////Pointer to the image data the timestamp will be read from
//														 const unsigned char *SrcImg,
/////The width and height of the input frame.
/////Note: Height should not include the encoded data row.
//														 int Width, 
//														 int Height
//														   );
//
/////Reads the embedded exposure time from a frame from a previously saved avi
///// \return The exposure time, in microseconds
//MS_CAMERACONTROL_API int MS_ReadExposureTimeFromSavedFrame(
/////Pointer to the image data the timestamp will be read from
//														 const unsigned char *SrcImg,
/////The width and height of the input frame
/////Note: Height should not include the encoded data row.
//														 int Width, 
//														 int Height
//														  );
//
//
//
//

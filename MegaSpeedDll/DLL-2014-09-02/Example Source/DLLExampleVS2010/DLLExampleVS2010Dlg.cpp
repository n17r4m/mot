// DLLExampleVS2010Dlg.cpp : implementation file

// This project gives some basic examples on how to connect to the camera, do a continuous or triggere capture, and download frames to PC RAM or an AVI.
// Error checking/handling is kept to a minimum for clarity



#include "stdafx.h"
#include "DLLExampleVS2010.h"
#include "DLLExampleVS2010Dlg.h"
#include "afxdialogex.h"

#include "DisplayWnd.h"
#include "MS_CameraControl.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif


// CDLLExampleVS2010Dlg dialog


/// This is the Camera ID value that we will use to identify the camera we want to connect to.
/// In these examples, the Camera ID is generated from the MAC Address of the camera that we want to connect to.\n
long g_CameraID = -1;

bool IsColorCamera = false;

bool IsCapturing = false;
bool IsDownloading = false;
bool DownloadComplete = false;
bool LastCapturePrePost = false;

CDisplayWnd *DispWindow = NULL;



bool Initalize();
bool FindAndConnectToCamera();
bool DoCapture(int Width, int Height, int Speed);
bool DoPrePostCapture(int Width, int Height, int Speed);
bool DoDownload();
bool DoDownload_PrePost();

void CallbackFrameDownloaded(long CameraID);



CDLLExampleVS2010Dlg::CDLLExampleVS2010Dlg(CWnd* pParent /*=NULL*/)
	: CDialogEx(CDLLExampleVS2010Dlg::IDD, pParent)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CDLLExampleVS2010Dlg::DoDataExchange(CDataExchange* pDX)
{
	CDialogEx::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(CDLLExampleVS2010Dlg, CDialogEx)
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_BTN_CAPTURE, &CDLLExampleVS2010Dlg::OnClickedBtnCapture)
	ON_BN_CLICKED(IDC_BTN_CONNECT, &CDLLExampleVS2010Dlg::OnClickedBtnConnect)
	ON_BN_CLICKED(IDC_BTN_DOWNLOAD, &CDLLExampleVS2010Dlg::OnClickedBtnDownload)
	ON_WM_TIMER()
	ON_WM_DESTROY()
	ON_BN_CLICKED(IDC_BTN_PREPOST, &CDLLExampleVS2010Dlg::OnClickedBtnPrepost)
END_MESSAGE_MAP()


const int POLL_TIMER_ID = 12345;


// CDLLExampleVS2010Dlg message handlers

BOOL CDLLExampleVS2010Dlg::OnInitDialog()
{
	CDialogEx::OnInitDialog();

	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon

	SetTimer(POLL_TIMER_ID, 1000, NULL);


	return TRUE;  // return TRUE  unless you set the focus to a control
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CDLLExampleVS2010Dlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialogEx::OnPaint();
	}
}

void CDLLExampleVS2010Dlg::OnDestroy()
{
	if(DispWindow != NULL)
	{
		DispWindow->DestroyWindow();
		delete DispWindow;
	}

    // When you are finished using the camera, call MS_CleanupCameraID() to release the camera ID and free the memory used by this camera's buffers
    MS_CleanupCameraID(g_CameraID);

    // When you are finished using the DLL, call MS_CloseDLL() to close the DLL and free all of the resources it is using.
    MS_CloseDLL();
	
	CDialogEx::OnDestroy();
}


// The system calls this function to obtain the cursor to display while the user drags
//  the minimized window.
HCURSOR CDLLExampleVS2010Dlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

void CDLLExampleVS2010Dlg::OnTimer(UINT_PTR nIDEvent)
{
	if(nIDEvent == POLL_TIMER_ID)
	{
		if(IsDownloading == true && DownloadComplete == true)
		{
			OnClickedBtnDownload();	//this will update the UI to indicate the download is completed
		}
	}

	CDialogEx::OnTimer(nIDEvent);
}

void CDLLExampleVS2010Dlg::OnClickedBtnConnect()
{
	int status = c_status_OK;

	if(Initalize() == false)
		return;

	//this can take some time, so doing it on a different thread with some sort of progress feedback might be desirable
	if(FindAndConnectToCamera() == false)
		return;

//for the purposes of the example, create a simple MFC window which will display the capture preview and download frames
//It is not necessary to use MFC, once the data is acquired from the camera it can be stored, processed or displayed however you desire
	CString strMyClass = AfxRegisterWndClass(CS_VREDRAW | CS_HREDRAW, LoadCursor(NULL, IDC_ARROW), 0, ::LoadIcon(NULL, IDI_APPLICATION));
	DispWindow = new CDisplayWnd();
	RECT DispWndRect = {0,0,800,600};
	DispWindow->CreateEx(0, strMyClass, L"Display", WS_OVERLAPPEDWINDOW|WS_VISIBLE, DispWndRect, NULL, 0);
//

	//use this to set a callback function which will be called whenever a new frame is downloaded from the capture. 
	//This might be a preview frame or a downloaded frame, depending on the current state of the camera.
	//The parameter passed to the callback function is: long CameraID
	MS_SetCallback_AcquiredNewFrame(g_CameraID, CallbackFrameDownloaded, &status);
	if( status != c_status_OK )
	{
		AfxMessageBox(L"Failed to set callback function\n");
		return;
	}

	IsColorCamera = MS_CheckIfCameraHasColor(g_CameraID);

	GetDlgItem(IDC_BTN_CONNECT)->EnableWindow(FALSE);
	GetDlgItem(IDC_BTN_CAPTURE)->EnableWindow(TRUE);

	if(MS_CheckIfCameraHasTriggerType(g_CameraID, c_TriggerTypePrePost))
		GetDlgItem(IDC_BTN_PREPOST)->EnableWindow(TRUE);
	
	GetDlgItem(IDC_BTN_DOWNLOAD)->EnableWindow(FALSE);
}

void CDLLExampleVS2010Dlg::OnClickedBtnCapture()
{
	int Width = 1280;
	int Height= 1020;
	int Speed = 30;

	if(IsCapturing == true)
	{
		//stop capturing
		int status = c_status_OK;
		MS_StopCaptureOrDownload( g_CameraID, &status );
		if( status != c_status_OK )
			return;

		IsCapturing = false;
		GetDlgItem(IDC_BTN_CAPTURE)->SetWindowText(L"Capture");
		GetDlgItem(IDC_BTN_DOWNLOAD)->EnableWindow(TRUE);
		GetDlgItem(IDC_BTN_PREPOST)->EnableWindow(TRUE);
	}
	else
	{
		//start capturing
		if(DoCapture(Width, Height, Speed) == false)
		{
			AfxMessageBox(L"Failed to start continuous capture");
			return;
		}
		LastCapturePrePost = false;
		IsCapturing = true;
		GetDlgItem(IDC_BTN_CAPTURE)->SetWindowText(L"Stop Capture");
		GetDlgItem(IDC_BTN_DOWNLOAD)->EnableWindow(FALSE);	//can't download when capturing
		GetDlgItem(IDC_BTN_PREPOST)->EnableWindow(FALSE);	//can't start pre/post trigger mode when in capture mode
	}
}

void CDLLExampleVS2010Dlg::OnClickedBtnPrepost()
{
	int Width = 1280;
	int Height= 720;
	int Speed = 60;

	if(IsCapturing == true)
	{
		//stop capturing
		int status = c_status_OK;
		MS_StopCaptureOrDownload( g_CameraID, &status );
		if( status != c_status_OK && status != c_status_CameraIsNotCapturing)
			return;

		IsCapturing = false;
		GetDlgItem(IDC_BTN_PREPOST)->SetWindowText(L"Pre/Post Trigger");
		GetDlgItem(IDC_BTN_DOWNLOAD)->EnableWindow(TRUE);
		GetDlgItem(IDC_BTN_CAPTURE)->EnableWindow(TRUE);
	}
	else
	{
		//start capturing
		if(DoPrePostCapture(Width, Height, Speed) == false)
		{
			AfxMessageBox(L"Failed to start Pre/Post Capture");
			return;
		}
		LastCapturePrePost = true;
		IsCapturing = true;
		GetDlgItem(IDC_BTN_PREPOST)->SetWindowText(L"Stop Capture");
		GetDlgItem(IDC_BTN_DOWNLOAD)->EnableWindow(FALSE);	//can't download when capturing
		GetDlgItem(IDC_BTN_CAPTURE)->EnableWindow(FALSE);	//can't start continuous capture when in pre/post trigger mode
	}
}

void CDLLExampleVS2010Dlg::OnClickedBtnDownload()
{
	if(IsDownloading == true)
	{
		//stop downloading, if it is still running
		if(MS_GetCaptureStatus(g_CameraID).IsCapturingOrDownloading)
		{
			int status = c_status_OK;
			MS_StopCaptureOrDownload( g_CameraID, &status );
			if( status != c_status_OK )
				return;
		}

	//need to change this to handle download completed
		IsDownloading = false;
		DownloadComplete = false;
		GetDlgItem(IDC_BTN_DOWNLOAD)->SetWindowText(L"Download");
		GetDlgItem(IDC_BTN_CAPTURE)->EnableWindow(TRUE);
	}
	else
	{
		//start downloading
		if(LastCapturePrePost == true)
		{	
			if(DoDownload_PrePost() == false)
			{
				AfxMessageBox(L"Failed To Download Pre/Post Capture");
				return;
			}
		}
		else
		{
			if(DoDownload() == false)
			{
				AfxMessageBox(L"Failed To Download capture");
				return;
			}
		}

		IsDownloading = true;
		GetDlgItem(IDC_BTN_DOWNLOAD)->SetWindowText(L"Stop Download");
		GetDlgItem(IDC_BTN_CAPTURE)->EnableWindow(FALSE);	//can't capture when downloading
	}
}


bool Initalize()
{
	int status = c_status_OK;
    MS_InitializeDLL(&status);	// call MS_InitializeDLL() to initialize the DLL.  If the DLL has already been initialized, then this will have no effect.

	// test if the DLL was initialized successfully
	if( status != c_status_OK && status != c_status_DLLAlreadyInitialized )
	{
		AfxMessageBox(L"Failed to initialize the DLL!\n");
		return false;
	}

	return true;
}

bool FindAndConnectToCamera()
{
	int status = c_status_OK;
	if( g_CameraID != -1 )
		return false;	//already connected to a camera

	
	//find the MAC Address of the only camera available on the network.
	int numCamerasFound = 0;
	char MacAddress[100];
	MS_FindAvailableCameraMACAddress(MacAddress, 100, &numCamerasFound, 1000);

	//check if any cameras were found
	if( numCamerasFound == 0 )
	{
		AfxMessageBox(L"No camera detected!\n");
		return false;
	}
	else if( numCamerasFound > 1 )
	{
		AfxMessageBox(L"More than one camera detected!\n");
		return false;
	}

	// next, initialize the camera ID, based on the camera's MAC Address
	g_CameraID = MS_InitializeCameraID(MacAddress, &status);

	// test if the camera ID was initialized successfully
	if( status != c_status_OK )
	{
		AfxMessageBox(L"Failed to initialize the camera ID!\n");
		g_CameraID = -1;
		return false;
	}
	
	// The camera ID has now been initialized.  You can now safely call the functions in this DLL that require a camera ID.

    // next, attempt to connect to the only camera available on the network.
    bool result = MS_ConnectToCamera(g_CameraID, 1000);

    // check if we connected to the camera successfully
    if( !result )
        AfxMessageBox(L"Failed to connect to the camera!\n");
	else
		AfxMessageBox(L"Connected to the camera\n");
       
	return result;
}

bool DoCapture(int Width, int Height, int CaptureSpeed)
{
	int status = c_status_OK;

//	// next, set the capture mode to Continuous Capture to camera RAM
	MS_SwitchToCaptureModeContinuous(g_CameraID, &status);
	if( status != c_status_OK )
		return false;


    //set the image size to the desired value
    MS_ChangeImageSize(g_CameraID, Width, Height, &status);
    if( status != c_status_OK )
        return false;

	//Note: when capturing at larger image sizes, the capture preview frames can be reduced in size from what the camera is actually capturing at
	int ImageWidth= MS_GetCurrentImageSize(g_CameraID).ImageWidthFromCamera;
	int ImageHeight = MS_GetCurrentImageSize(g_CameraID).ImageHeightFromCamera;


    // next, set the basic capture settings
    StructBasicCaptureSettings BasicCaptureSettings = MS_GetBasicCaptureSettings(g_CameraID);

    BasicCaptureSettings.CaptureSpeed = CaptureSpeed;
    BasicCaptureSettings.ExposureTime = MS_CalculateMaxExposureTime( g_CameraID, BasicCaptureSettings.CaptureSpeed );

    MS_SetBasicCaptureSettings(g_CameraID, BasicCaptureSettings, true, &status);
    if( status != c_status_OK )
        return false;

    // next, change the advanced capture settings
    StructAdvancedCaptureSettings AdvancedCaptureSettings = MS_GetAdvancedCaptureSettings(g_CameraID);
    AdvancedCaptureSettings.UsePCTime          = true;
    AdvancedCaptureSettings.InvertStrobe       = false;
    AdvancedCaptureSettings.InvertTrigger      = false;
    AdvancedCaptureSettings.TriggerSensitivity = 0;
    MS_SetAdvancedCaptureSettings(g_CameraID, AdvancedCaptureSettings, true, &status);
    if( status != c_status_OK )
        return false;

	//Note: these do not affect capture preview or downloaded frames. They will affect using the DLL to save Video/Images
	StructOverlaySettings OverlaySettings = MS_GetOverlaySettings(g_CameraID, &status);
	OverlaySettings.EnableOverlay = false;	
	MS_SetOverlaySettings(g_CameraID, OverlaySettings, true, &status);

    // next, start the capture
    MS_StartCaptureOrDownload( g_CameraID, &status );
    if( status != c_status_OK )
        return false;

	return true;
}

bool DoPrePostCapture(int Width, int Height, int CaptureSpeed)
{
	//Note: This example relies on the software sending a stop command
	//The camera will stop recording after the specified number of frames have been captured, 
	//but this example software does not monitor to see when that has happened and update it's UI accordingly.
	//Also note that the stop capture button can be used at any time after the capture has started, 
	//there is no need to wait for the post trigger frames to be captured if they are not wanted.


	int status = c_status_OK;

	//set the capture mode to pre/post trigger
	MS_SwitchToCaptureModeByTrigger(g_CameraID, c_TriggerTypePrePost, &status);
	if( status != c_status_OK )
		return false;

	//set the image size to the desired value
	MS_ChangeImageSize(g_CameraID, Width, Height, &status);
	if( status != c_status_OK )
		return false;


	long MaxFrames = MS_CalculateTotalFramesInCameraRAM(g_CameraID);
	long PostTriggerFrames = MaxFrames-100;

	//When the camera starts capturing, it will capture continuously until a trigger pulse occurs.
	//Then it will capture the specified number of post-trigger frames and stop.
	//Any space in the camera memory not reserved for post-trigger frames will either contain pre-trigger frames 
	//or nothing, if the trigger happens before the space for pre-trigger frames is filled.
	//The capture can also be stopped by software at any time, if desired.
	MS_SetPostTriggerFrames(g_CameraID, PostTriggerFrames, &status);

    // next, set the basic capture settings
    StructBasicCaptureSettings BasicCaptureSettings = MS_GetBasicCaptureSettings(g_CameraID);

    BasicCaptureSettings.CaptureSpeed = CaptureSpeed;
    BasicCaptureSettings.ExposureTime = MS_CalculateMaxExposureTime( g_CameraID, BasicCaptureSettings.CaptureSpeed );

    MS_SetBasicCaptureSettings(g_CameraID, BasicCaptureSettings, true, &status);
    if( status != c_status_OK )
        return false;

    // next, change the advanced capture settings
    StructAdvancedCaptureSettings AdvancedCaptureSettings = MS_GetAdvancedCaptureSettings(g_CameraID);
    AdvancedCaptureSettings.UsePCTime          = true;
    AdvancedCaptureSettings.InvertStrobe       = false;
    AdvancedCaptureSettings.InvertTrigger      = false;

	//Note: This value can be increased if noise or anything else is causing spurious trigger signals, but it will add a corresponding amount of latency 
	//It is generally not necessary to increase this, or use large increases.
    AdvancedCaptureSettings.TriggerSensitivity = MS_CalculateMinTriggerSensitivity(g_CameraID);

    MS_SetAdvancedCaptureSettings(g_CameraID, AdvancedCaptureSettings, true, &status);
    if( status != c_status_OK )
        return false;

	//Note: these do not affect capture preview or downloaded frames. They will affect using the DLL to save Video/Images
	StructOverlaySettings OverlaySettings = MS_GetOverlaySettings(g_CameraID, &status);
	OverlaySettings.EnableOverlay = false;	
	MS_SetOverlaySettings(g_CameraID, OverlaySettings, true, &status);

    // next, start the capture
    MS_StartCaptureOrDownload( g_CameraID, &status );
    if( status != c_status_OK )
        return false;

	return true;
}

bool DoDownload()
{
	int status = c_status_OK;
    MS_SwitchToDownloadToPCMode(g_CameraID, &status);
    if( status != c_status_OK )
        return false;

    // check what the download image size will be - it will be the same size as the images captured to camera RAM, since we are now in download mode.
    int ImageWidth= MS_GetCurrentImageSize(g_CameraID).ImageWidthFromCamera;
    int ImageHeight = MS_GetCurrentImageSize(g_CameraID).ImageHeightFromCamera;

    // next, change the download settings
    StructDownloadSettings DownloadSettings = MS_GetDownloadSettings(g_CameraID);

	// download at maximum speed, may want to lower this for congested network or slow PC; or if frames are being dropped
    DownloadSettings.DownloadSpeed = MS_CalculateMaxDownloadSpeed(g_CameraID, ImageWidth, ImageHeight);
    DownloadSettings.DownloadStartPos = 0; // start at the first frame in camera RAM
    DownloadSettings.DownloadEndPos = MS_GetCaptureStatus(g_CameraID).LastCaptureStopPos; // download all the frames from the previous capture
    DownloadSettings.UseDownloadEndPos = true; // stop downloading when the download end frame is reached

//rather than saving to hard drive, save to PC RAM instead and just display the frames
//    DownloadSettings.DestFileName = "DownloadFromCameraRAM.avi";
//    DownloadSettings.DestFileType = c_DownloadToAVI;
	DownloadSettings.DestFileType = c_DownloadToRAM;

    MS_SetDownloadSettings(g_CameraID, DownloadSettings, true, &status);
    if( status != c_status_OK )
        return false;

    // next, start the download
    MS_StartCaptureOrDownload( g_CameraID, &status );
    if( status != c_status_OK )
        return false;

 	return true;
}

bool DoDownload_PrePost()
{
	int status = c_status_OK;
    MS_SwitchToDownloadToPCMode(g_CameraID, &status);
    if( status != c_status_OK )
        return false;

//after a pre/post trigger mode capture these can be checked to determine what happened and when
	int PostTriggerStartPos    = MS_GetPostTriggerStartPos(g_CameraID);
	bool PrePostLooped		   = MS_GetPostTriggerLoopedThrough(g_CameraID);

	if(PostTriggerStartPos <= 0)
	{
		AfxMessageBox(L"No Trigger was received, skipping download");
		DownloadComplete = true;
		return true;
	}

	int LastCaptureStopPos     = MS_GetCaptureStatus(g_CameraID).LastCaptureStopPos;
	int TotalFramesInCameraRAM = MS_CalculateTotalFramesInCameraRAM(g_CameraID);

	//now need to adjust the download range
	StructDownloadSettings DownloadSettings = MS_GetDownloadSettings(g_CameraID);

	//post-trigger frames will be PostTriggerStartPos to LastCaptureStopPos
	//pre-trigger frames will be from 0 to PostTriggerStartPos if the capture didn't loop
	//or from LastCaptureStopPos+1 to PostTriggerStartPos if the capture did loop

	//this example will download (up to) 100 pre-trigger frames and 200 post-trigger frames
	//can be less if fewer frames were captured
	const int PreTrigFrames = 100;
	const int PostTrigFrames = 200;

//this would download all valid frames
//	if(PrePostLooped == true)
//	{
//		DownloadSettings.DownloadStartPos = LastCaptureStopPos+1;	//camera will loop back to start of RAM and continue to LastCaptureStopPos while downloading
//		DownloadSettings.DownloadEndPos = LastCaptureStopPos;
//	}
//	else
//	{
//		DownloadSettings.DownloadStartPos = 0;
//		DownloadSettings.DownloadEndPos = LastCaptureStopPos;
//	}

	DownloadSettings.DownloadStartPos = PostTriggerStartPos-PreTrigFrames;
	DownloadSettings.DownloadEndPos = PostTriggerStartPos+PostTrigFrames;
	if(DownloadSettings.DownloadEndPos > LastCaptureStopPos && PrePostLooped == false)
		DownloadSettings.DownloadEndPos = LastCaptureStopPos;	//there were less than <PostTrigFrames> post-trigger frames captured

	if(DownloadSettings.DownloadStartPos<0)
		DownloadSettings.DownloadStartPos = 0;
	if(DownloadSettings.DownloadEndPos > TotalFramesInCameraRAM)
		DownloadSettings.DownloadEndPos -= TotalFramesInCameraRAM;	//wrapping


	// check what the download image size will be - it will be the same size as the images captured to camera RAM, since we are now in download mode.
	int ImageWidth= MS_GetCurrentImageSize(g_CameraID).ImageWidthFromCamera;
	int ImageHeight = MS_GetCurrentImageSize(g_CameraID).ImageHeightFromCamera;

	// download at maximum speed, may want to lower this for congested network or slow PC; or if frames are being dropped
	DownloadSettings.DownloadSpeed = MS_CalculateMaxDownloadSpeed(g_CameraID, ImageWidth, ImageHeight);
	DownloadSettings.UseDownloadEndPos = true; // stop downloading when the download end frame is reached

	//save an AVI with raw data in it to the hard drive.
	DownloadSettings.DestFileName = "PrePostDownload.avi";
	DownloadSettings.DestFileType = c_DownloadToAVI;

	MS_SetDownloadSettings(g_CameraID, DownloadSettings, true, &status);
	if( status != c_status_OK )
		return false;

	// next, start the download
	MS_StartCaptureOrDownload( g_CameraID, &status );
	if( status != c_status_OK )
		return false;

	return true;
}


//Note: It is important that this callback (and others) do not take too long to execute or it could result in dropped frames and other problems
//If longer frame processing times are required:
//download speeds can be slowed down using MS_CalculateMinDownloadSpeed() and MS_SetDownloadSettings()
//data can be copied from the internal buffers to application controlled buffers for processing at a different time or on a different thread
//or data can be saved to disk for later offline processing/analysis

void CallbackFrameDownloaded(long CameraID)
{
static int LastFrameNumDisplayed = 0;

	if(DispWindow != NULL && DispWindow->GetSafeHwnd() != NULL)
	{
		StructBufferStatus BufferStatus = MS_GetBufferStatus(g_CameraID);

        int LastFrameNumSavedToRAM = BufferStatus.LastValidFrame;

        // if a new preview frame has been saved to PC RAM, then save it to a bitmap file.
        if( LastFrameNumSavedToRAM != LastFrameNumDisplayed )
        {
			char TimeStr[100];
			int Speed = MS_ReadCaptureSpeedFromFrame(g_CameraID, BufferStatus.ImageBuffers[LastFrameNumSavedToRAM]);
			MS_ReadTimeStampFromFrame(g_CameraID, TimeStr, 100, BufferStatus.ImageBuffers[LastFrameNumSavedToRAM]);

			//update the display window
			CString FrameInfoStr;
			if(IsDownloading)
				FrameInfoStr.Format(L"[Download] Capture FPS: %d, Time: %S", Speed, TimeStr);
			else if(IsCapturing)
				FrameInfoStr.Format(L"[Capture preview] Capture FPS: %d, Time: %S", Speed, TimeStr);
			else
				FrameInfoStr = L"Camera Idle";

			DispWindow->SetWindowText(FrameInfoStr);

			StructCurrentImageSize CurrImgSize = MS_GetCurrentImageSize(g_CameraID);
			int ImageWidth = CurrImgSize.ImageWidthFromCamera;
			int ImageHeight = CurrImgSize.ImageHeightFromCamera;

			if(IsColorCamera)	//display color data
			{
				BYTE *Buffer = new BYTE[ImageWidth*ImageHeight*4];
				MS_GetColorImage(g_CameraID, BufferStatus.ImageBuffers[LastFrameNumSavedToRAM], (unsigned long*)Buffer);
				DispWindow->SetInputData32Bit(ImageWidth, ImageHeight, (unsigned __int32*)Buffer);

				delete[] Buffer;
			}
			else //display raw/grayscale data
			{
				DispWindow->SetInputData8Bit(ImageWidth, ImageHeight, BufferStatus.ImageBuffers[LastFrameNumSavedToRAM]);
			}
		}

		if(IsDownloading == true && BufferStatus.TotalFramesSavedToBuffer >= MS_GetDownloadStatus(g_CameraID).FramesToDownload)
			DownloadComplete = true;
	}
}


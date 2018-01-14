/*!
\file

\short The header file for the Mega Speed Camera Control DLL.

\include MS_CameraControl.h
*/

//*******************************************

#if !defined(AFX_MSCAMERACONTROL_H_INCLUDED_)
#define AFX_MSCAMERACONTROL_H_INCLUDED_


// The following ifdef block is the standard way of creating macros which make exporting
// from a DLL simpler. All files within this DLL are compiled with the MS_CAMERACONTROL_EXPORTS
// symbol defined on the command line. this symbol should not be defined on any project
// that uses this DLL. This way any other project whose source files include this file see
// MS_CAMERACONTROL_API functions as being imported from a DLL, wheras this DLL sees symbols
// defined with this macro as being exported.
#ifdef MS_CAMERACONTROL_EXPORTS
  #define MS_CAMERACONTROL_API __declspec(dllexport)
#else
  #ifdef MS_CAMERACONTROL_TESTING
	#define MS_CAMERACONTROL_API
  #else
	#define MS_CAMERACONTROL_API __declspec(dllimport)
  #endif
#endif


#include <string>


/*! \mainpage Mega Speed Camera Control DLL Version 2.5 Documentation

\section section1 Section 1: Introduction

\attention This DLL is still in development.  Some details may change in future versions of this DLL.

<b> </b>

\attention This DLL requires drivers installed with the Camera Control software, so that install process should be completed before using the DLL.\n
The Mega Speed AVI Player is also required to play back the AVI files saved by the Mega Speed cameras DLL.\n
This DLL additionally requires the "Microsoft Visual C++ 2010 SP1 Redistributable Package (x86)" which is freely available from Microsoft if it is not already installed on your system.

<b> </b>


\attention It is recommended to view the documentation and code for the DLL Example project before getting too far into this documentation to help gain an understanding of where to start.

<b> </b>



The following documentation is intended to provide the end user with sufficient information required to control the MS50K, MS55K, MS70K, MS75K, MS80K, and MS85K camera.

\n
\n

<b>Notes on the DLL:</b>\n

<b>1.</b> 
\copydoc autoshutdownmode
\n
<b>2.</b> 
Formula to calculate the total number of frames in camera and the total recording time:\n
The cameras have internal RAM which can hold a certain amount of frames during high speed capture.\n
You can call MS_CalculateTotalFramesInCameraRAM() to determine how many frames can be held in the RAM at a given image size.\n
Dividing the number of frames by the capture speed in frames per second yields the amount of time it takes to fill the camera's memory.
These figures are useful when doing a high speed capture to camera memory and downloading from camera memory to PC memory.\n
\n
<b>3.</b>
The camera ID data for each camera is stored inside the DLL.\n
If you purchase additional cameras, then you will also be sent an updated version of the DLL, which has the camera ID data for the new cameras.\n
This updated DLL will function exactly the same as the previous version of the DLL, but will include the updated camera ID data.\n
\n
<b>4.</b> \copydoc previoussettingsfile
\n
<b>5.</b> \copydoc indeo
\n

\n\n\n\n\n
***************************************************************************************************************************************

\section section2 Section 2: How to use this DLL in your project

1. Copy MS_CameraControl.h and MS_CameraControl.lib to your project folder.
2. Include the MS_CameraControl.h header into the project.
3. Add the MS_CameraControl.lib to the linker project settings.
4. The MS_CameraControl.dll must be in the application search path, typically the same folder as the application, or for development in the project folder.

The sample project included shows this.

\n\n\n\n\n
***************************************************************************************************************************************

\section section3 Section 3:  Camera Modes

\copydoc cameramodes

See the \ref cameramodes documentation for more information.

\n\n\n\n\n
***************************************************************************************************************************************

\section section4 Section 4:  Camera Control Structs

\copydoc cameracontrolstructs

See the \ref cameracontrolstructs documentation for more information.

\n\n\n\n\n
***************************************************************************************************************************************

\section section5 Section 5:  Camera Constants

\copydoc cameraconstants

See the \ref cameraconstants documentation for more information.

\n\n\n\n\n
***************************************************************************************************************************************

\section section6 Section 6:  Camera Control Functions

\copydoc cameracontrolfunctions

See the \ref cameracontrolfunctions documentation for more information.

\n\n\n\n\n
***************************************************************************************************************************************

\section section7 Section 7:  Callback Functions

\copydoc callbackfunctions

See the \ref callbackfunctions documentation for more information.


\n\n\n\n\n\n\n\n\n\n\n
***************************************************************************************************************************************
*/


/***************************************************************************************************************************************/

/*! \defgroup cameracontrolstructs Camera Control Structs

These structs are used by the functions in this DLL that get and set the camera's parameters.\n
\n
These structs are divided into the following categories:\n
\n
\ref camerasettingstructs
\n
\copydoc camerasettingstructs
\n
\n
\ref camerastatusstructs
\n
\copydoc camerastatusstructs
\n
\n
\ref otherstructs
\n
\copydoc otherstructs
\n

@{
*/

/*! \defgroup camerasettingstructs Camera Setting Structs

These structs are used to read or write the camera's settings.

The following structs are in this category:\n
\n
\ref ::StructBasicCaptureSettings
\n
\ref ::StructAdvancedCaptureSettings
\n
\ref ::StructDownloadSettings
\n
\ref ::StructColorSettings
\n
\ref ::StructOverlaySettings
\n
\ref ::StructAVIFileSettings
\n
\ref ::StructImageFileSettings
\n
\ref ::StructAutoDownloadSettings
\n
\ref ::StructMultiSpeedSettings
\n
\ref ::StructBinningSettings
\n



@{
*/

/// Basic Capture Settings

/// This struct is used by MS_SetBasicCaptureSettings() to set the camera's basic capture settings.\n
/// This struct is also used by MS_GetBasicCaptureSettings() to report the camera's current basic capture settings.

typedef struct _StructBasicCaptureSettings
{
	/// The camera's capture speed, in frames per second.

	/// Use the functions MS_CalculateMinCaptureSpeed() and MS_CalculateMaxCaptureSpeed() to calculate the allowed values for CaptureSpeed.\n
	int CaptureSpeed;

	/// The camera's exposure time, in microseconds.

	/// Use the functions MS_CalculateMinExposureTime() and MS_CalculateMaxExposureTime() to calculate the allowed values for ExposureTime.\n
	int ExposureTime;

	/// The camera's gain value.

	/// Use the functions MS_CalculateMinGainValue() and MS_CalculateMaxGainValue() to calculate the allowed values for GainValue.\n
	int GainValue;

} StructBasicCaptureSettings;


/// Advanced Capture Settings

/// This struct is used by MS_SetAdvancedCaptureSettings() to set the camera's advanced capture settings.\n
/// This struct is also used by MS_GetAdvancedCaptureSettings() to report the camera's current advanced capture settings.

typedef struct _StructAdvancedCaptureSettings
{
	/// Use PC Time or IRIG time

	/// Set this to <b>true</b> if you want the camera to use the PC's internal clock to generate each frame's timestamp.\n
	/// Set this to <b>false</b> if you want the camera to use camera's IRIG signal to generate each frame's timestamp.\n
	/// If you set this to <b>false</b>, then the timestamp feature will not work unless the camera receives a valid IRIG signal.\n
	bool UsePCTime;

	/// Invert Strobe

	/// Set this to <b>true</b> if you want invert the strobe signal that the camera sends out.\n
	/// Set this to <b>false</b> if you do not want invert the strobe signal that the camera sends out.\n
	bool InvertStrobe;

	/// Invert Trigger

	/// Set this to <b>true</b> if you want to invert the trigger signal that the camera receives.\n
	/// Set this to <b>false</b> if you do not want to invert the trigger signal that the camera receives.\n
	///
	/// \attention If you change this value while the camera is armed, then the camera may interpret this as a trigger pulse, and start capturing!\n
	bool InvertTrigger;

	/// The sensitivity of the trigger input.

	/// Trigger pulses shorter than this length will be ignored.\n
	/// Use the function MS_CalculateMaxTriggerSensitivity() and MS_CalculateMinTriggerSensitivity() to calculate the allowed values for TriggerSensitivity.\n
	/// Use the function MS_AdjustTriggerSensitivityFromRawValueToMilliseconds() to convert this raw value used by the camera into the number of milliseconds for the delay.\n
	/// Use the function MS_AdjustTriggerSensitivityFromMillisecondsToRawValue() to convert the desired number of milliseconds for the delay into the raw value used by the camera.\n
	///
	/// \attention The trigger pulse "seen" by the camera is delayed by this value.  Therefore, the camera's response to the start / stop pulse will be delayed by this value.\n
	int TriggerSensitivity;

} StructAdvancedCaptureSettings;


/// Download Settings

/// This struct is used by MS_SetDownloadSettings() to set the camera's download settings.\n
/// This struct is also used by MS_GetDownloadSettings() to report the camera's current download settings.

typedef struct _StructDownloadSettings
{
	/// The camera's download speed, in frames per second.

	/// Use the functions MS_CalculateMinDownloadSpeed() and MS_CalculateMaxDownloadSpeed() to calculate the allowed values for StructDownloadSettings::DownloadSpeed.\n
	/// The download speed can safely be changed while a download is in progress.\n
	int DownloadSpeed;

	/// The number of the first frame to download from camera RAM or camera Flash (in camera models that have internal Flash RAM).

	/// Use the function MS_CalculateTotalFramesInCameraRAM() to check how many frames there are in camera RAM, at the current image size\n
	int DownloadStartPos;

	/// The number of the last frame to download from camera RAM or camera Flash (in camera models that have internal Flash RAM).

	/// If the end position is lower than the start position, then the download will start from the start frame, continue to the end of camera RAM,
	///  then loop back to the first frame in camera RAM, and continue until the end frame is reached.\n
	/// \n
	/// If StructDownloadSettings::UseDownloadEndPos is set to <b>false</b>, then this value will be ignored, and the download will start from the start frame, continue to the end of camera RAM,
	///  then loop back to the first frame in camera RAM, and continue until the start frame is reached, meaning that every frame in camera RAM will be downloaded.\n
	int DownloadEndPos;

	/// Use Download End Position

	/// If this is <b>true</b>, then the download will start from StructDownloadSettings::DownloadStartPos and end at StructDownloadSettings::DownloadEndPos.\n
	/// If this is <b>false</b>, then the download will start from StructDownloadSettings::DownloadStartPos and end at StructDownloadSettings::DownloadStartPos, meaning that every frame in camera RAM will be downloaded.\n
	bool UseDownloadEndPos;

	/// Destination File Name

	/// This is the name of the file that you want to download to, if StructDownloadSettings::DestFileType is not set to ::c_DownloadToRAM\n
	/// If the file already exists, it will not be overwritten.  Instead, a number will be appended to the end of the file name.\n
	std::string DestFileName;

	/// The type of file that you want to download to.

	/// If you select ::c_DownloadToRAM, then the data will be downloaded to the PC's RAM, but not saved to a file.\n
	/// \n
	/// For a list of allowed values, see \ref downloaddestinationtypes\n
	int DestFileType;

} StructDownloadSettings;


/// Color Settings

/// This struct is used by MS_SetColorSettings() to set the camera's color settings.\n
/// This struct is also used by MS_GetColorSettings() to report the camera's current color settings.

/// The Bayer values will be initialized to an appropriate default value when you connect to the camera

typedef struct _StructColorSettings
{
	/// The color mode that the images from the camera will be displayed in.

	/// This is also the mode that the images will be saved in, when saved to BMP, JPG, TIF, or AVI files.\n
	/// No matter which display mode you choose, the images will be stored in raw format, and will not be converted to another format until they are displayed\n
	/// \n
	/// For a list of allowed values, see \ref colormodes
	int DisplayMode;

	/// Bayer Values

	/// These are the coefficients used by the bayer algorithm when converting the image from 8-bit raw data to 32-bit color.\n
	/// These value determines how much red, green, and blue will apear in the processed color images.  The recommended range for this value is 0-255, but any integer value may be used.\n
	int BayerRed;
	/// See StructColorSettings::BayerRed
	int BayerGreen;
	/// See StructColorSettings::BayerRed
	int BayerBlue;

	/// This is the gamma value for the bayer algorithm.  The recommended value is 1, but any double value greater than 0 can be used.
	double BayerGamma;

	/// Intensity Values

	/// These are the coefficients used by the modified bayer algorithm when processing the raw image when StructColorSettings::DisplayMode is ::c_ColorModeGamma.\n
	/// This value works the same way as the red, green, and blue values in the normal bayer algorithm, except that this value applies to all 3 color channels.\n
	int BayerIntensity;
	/// This value works the same way as StructColorSettings::BayerGamma, but is only used when processing the raw image when StructColorSettings::DisplayMode is ::c_ColorModeGamma.
	double BayerRawGamma;

} StructColorSettings;





/// Overlay Settings

/// This struct is used by MS_SetOverlaySettings() to set the camera's overlay settings.\n
/// This struct is also used by MS_GetOverlaySettings() to report the camera's current overlay settings.

typedef struct _StructOverlaySettings
{
	/// If this is set to <b>true</b>, then the camera's marker data will be displayed, if one of the four overlay slots has been assigned to it.
	bool MarkerSelected           ;
	/// If this is set to <b>true</b>, then the camera's gigabit timestamp will be displayed, if one of the four overlay slots has been assigned to it.

	/// \attention This feature does nothing in this version of the DLL.\n
	bool GigabitTimeStampSelected ;
	/// If this is set to <b>true</b>, then the camera's IRIG timestamp data will be displayed, if one of the four overlay slots has been assigned to it.
	bool IRIGTimeStampSelected    ;
	/// If this is set to <b>true</b>, then the camera's capture start date will be displayed, if one of the four overlay slots has been assigned to it.

	/// \attention This feature does nothing in this version of the DLL.\n
	bool CaptureStartDateSelected ;
	/// If this is set to <b>true</b>, then the camera's capture speed will be displayed, if one of the four overlay slots has been assigned to it.
	bool CaptureSpeedSelected     ;
	/// If this is set to <b>true</b>, then the camera's exposure time will be displayed, if one of the four overlay slots has been assigned to it.
	bool ExposureTimeSelected     ;
	/// If this is set to <b>true</b>, then StructOverlaySettings::CustomDataString1 will be displayed, if one of the four overlay slots has been assigned to it.
	bool Custom1Selected          ;
	/// If this is set to <b>true</b>, then StructOverlaySettings::CustomDataString2 will be displayed, if one of the four overlay slots has been assigned to it.
	bool Custom2Selected          ;
	/// If this is set to <b>true</b>, then the camera's AtoD Data will be displayed, if one of the four overlay slots has been assigned to it.
	bool AtoDDataSelected         ;
	/// If this is set to <b>true</b>, then camera's RS422 Data will be displayed, if one of the four overlay slots has been assigned to it.
	bool RS422DataSelected        ;

	/// The string to display as "Custom Data 1".  If this string is longer than 38 characters, then the extra characters will be cut off.
	std::string CustomDataString1;

	/// The string to display as "Custom Data 2".  If this string is longer than 38 characters, then the extra characters will be cut off.
	std::string CustomDataString2;

	/// These "overlay choice" variables determine which overlay value is displayed in each of the four available positions.

	/// For a list of allowed values, see \ref overlaytypes
	int OverlayChoiceTopLeft;
	/// see StructOverlaySettings::OverlayChoiceTopLeft
	int OverlayChoiceTopRight;
	/// see StructOverlaySettings::OverlayChoiceTopLeft
	int OverlayChoiceBottomLeft;
	/// see StructOverlaySettings::OverlayChoiceTopLeft
	int OverlayChoiceBottomRight;

	/// Enable Overlay

	/// If this is <b>true</b>, then the MS_DoPostProcessing() functions will embed the overlay data to the image.\n
	/// Also, if this is set to <b>true</b>, then the overlay data will be embedded into any BMP, JPG, or TIF files saved to the hard drive.\n
	/// Also, if this is set to <b>true</b>, then the overlay data will be displayed in a saved AVI file, if it is opened in the Mega Speed AVI Player.\n
	bool EnableOverlay;

} StructOverlaySettings;


/// AVI File Settings

/// This struct is used by MS_SetAVIFileSettings() to set the camera's AVI file settings.\n
/// This struct is also used by MS_GetAVIFileSettings() to report the camera's current AVI file settings.

typedef struct _StructAVIFileSettings
{
	/// The quality setting for compressed AVI files.

	/// The default value is 60, which gives a good balance between image quality and file size.\n
	/// Higher values give higher quality, and larger files.\n
	int AVIFileQuality;

	/// This string is attached to the next AVI file that is saved to the hard drive.

	/// This note can be viewed in the AVI note viewer in the Mega Speed AVI Player.\n
	std::string AVIAttachedNote;

	/// The filename that you want to save the next AVI file to.
	std::string AVIFileName;

	/// The first frame from StructBufferStatus::ImageBuffers that will be saved to the AVI file by the MS_SaveToAVI() function.

	/// You do not need to set this manually.  It will automatically set to the FirstFrame parameter passed to the MS_SaveToAVI() function.\n
	int AVIFirstFrame;

	/// The last frame from StructBufferStatus::ImageBuffers that will be saved to the AVI file by the MS_SaveToAVI() function.

	/// You do not need to set this manually.  It will automatically set to the LastFrame parameter passed to the MS_SaveToAVI() function.\n
	int AVILastFrame;

	/// If this is <b>true</b>, then the AVI file saved by the MS_SaveToAVI() function will be compressed.

	/// You do not need to set this manually.  It will automatically set to the isCompressed parameter passed to the MS_SaveToAVI() function.\n
	bool AVIIsCompressed;

} StructAVIFileSettings;


/// Image File Settings

/// This struct is used by MS_SetImageFileSettings() to set the camera's image file settings.\n
/// This struct is also used by MS_GetImageFileSettings() to report the camera's current image file settings.

typedef struct _StructImageFileSettings
{
	/// The quality setting for compressed JPEG files.

	/// The default value is 60, which gives a good balance between image quality and file size.\n
	/// Higher values give higher quality, and larger files.\n
	int JPGFileQuality;

	/// TIF File Is Compressed

	/// If this is set to <b>true</b>, then the TIF files will be saved with LZW compression.\n
	/// If this is set to <b>false</b>, then the TIF files will be saved in raw data.\n
	/// The default value is <b>true</b>.\n
	bool TIFFileIsCompressed;

	/// The filename that you want to save the next image file to.
	std::string ImageFileName;

	/// The first frame from StructBufferStatus::ImageBuffers that will be saved to the image file by the MS_SaveToImageFile() function.

	/// You do not need to set this manually.  It will automatically set to the FirstFrame parameter passed to the MS_SaveToImageFile() function.\n
	int ImageFileFirstFrame;

	/// The last frame from StructBufferStatus::ImageBuffers that will be saved to the image file by the MS_SaveToImageFile() function.

	/// You do not need to set this manually.  It will automatically set to the LastFrame parameter passed to the MS_SaveToImageFile() function.\n
	int ImageFileLastFrame;

	/// Determines the type of image file to save to, using MS_SaveToImageFile()

	/// You do not need to set this manually.  It will automatically set to the imageType parameter passed to the MS_SaveToImageFile() function.\n
	/// \n
	/// For a list of allowed values, see \ref imagefiletypes
	int ImageFileType;

} StructImageFileSettings;


/// Auto-Download Settings

/// This struct is used by MS_SetAutoDownloadSettings() to set the camera's auto-download settings.\n
/// This struct is also used by MS_GetAutoDownloadSettings() to report the camera's current auto-download settings.

typedef struct _StructAutoDownloadSettings
{
	/// The download speed to use for the auto-download process, in frames per second.

	/// Use the functions MS_CalculateMinDownloadSpeed() and MS_CalculateMaxDownloadSpeed() to calculate the allowed values for StructAutoDownloadSettings::AutoDownloadSpeed.\n
	/// If StructAutoDownloadSettings::AutoDownloadAutoAdjustSpeed is set to <b>true</b>, then this value is ignored.\n
	int AutoDownloadSpeed;

	/// The number of the first frame to download from camera RAM, for the auto-download process.

	/// Use the function MS_CalculateTotalFramesInCameraRAM() to check how many frames there are in camera RAM, at the current image size\n
	/// If AutoDownloadAutoAdjustFrames is set to <b>true</b>, then this value is ignored.\n
	int AutoDownloadStartFrame;

	/// The number of the last frame to download from camera RAM, for the auto-download process.

	/// Use the function MS_CalculateTotalFramesInCameraRAM() to check how many frames there are in camera RAM, at the current image size\n
	/// If StructAutoDownloadSettings::AutoDownloadAutoAdjustFrames is set to <b>true</b>, then this value is ignored.\n
	int AutoDownloadEndFrame;

	/// The type of file that you want to download to, for the auto-download process.

	/// If you select ::c_DownloadToRAM, then the data will be downloaded to the PC's RAM, but not saved to a file.\n
	/// \n
	/// For a list of allowed values, see \ref downloaddestinationtypes
	int AutoDownloadFileType;

	/// Auto-Download File Name

	/// The name of the file that you want to download to, if StructDownloadSettings::DestFileType is not set to ::c_DownloadToRAM, for the auto-download process.\n
	/// If the file already exists, it will not be overwritten.  Instead, a number will be appended to the end of the file name.\n
	std::string AutoDownloadFileName;

	/// Auto-Adjust Download Speed for Auto-Download

	/// If this is set to <b>true</b>, then the auto-download will attempt to use the maximum possible speed, and will throttle back if the CPU or hard drive are not keeping up with the download.\n
	/// If this is set to <b>false</b>, then the auto-download will attempt to use the StructAutoDownloadSettings::AutoDownloadSpeed value for the speed,
	///  but will still throttle back if the CPU or hard drive are not keeping up with the download.\n
	bool AutoDownloadAutoAdjustSpeed;

	/// Auto-Adjust Frames for Auto-Download

	/// If this is set to <b>true</b>, then the auto-download process will download all of the frames that were saved to camera RAM by the previous capture.\n
	/// The frames will be downloaded in the order that they were captured, starting from the first frame that was captured and ending with the last frame that was captured.\n
	/// If the previous capture did not fill all of camera RAM, then only the frames from that capture will be downloaded.\n
	/// If the previous capture looped through camera RAM, then the download will start from the oldest frame that was not overwritten, and end at the last frame captured.\n
	/// If this is set to <b>false</b>, then the auto-download will start at StructAutoDownloadSettings::AutoDownloadStartFrame, and end at StructAutoDownloadSettings::AutoDownloadEndFrame.\n
	bool AutoDownloadAutoAdjustFrames;

	/// Auto-Close Download Manager for Auto-Download

	/// If this is set to <b>true</b>, then the DLL will automatically return StructCameraStatus::CameraMode to the previous capture mode when the auto-download is finished.\n
	/// If this is set to <b>false</b>, then the DLL will leave StructCameraStatus::CameraMode as ::c_CameraModeDownloadToPC when the auto-download is finished.\n
	bool AutoDownloadAutoCloseDLManager;

	/// Auto-Rearm Camera for Auto-Download

	/// If this is set to <b>true</b>, then the camera will automatically be sent a start command when the auto-download is finished, and StructCameraStatus::CameraMode was returned to its previous capture mode.\n
	/// If this is set to <b>false</b>, then the camera will not automatically be sent a start command when the auto-download is finished.\n
	/// If StructAutoDownloadSettings::AutoDownloadAutoCloseDLManager is set to <b>false</b>, then this value will automatically be set to <b>false</b>.\n
	bool AutoDownloadAutoRearmCamera;

	/// Enable Auto-Download to PC

	/// If this is set to <b>true</b>, then after the next capture is finshed, the auto-download process will begin.\n
	/// If this is set to <b>false</b>, then the auto-download process will not be started.\n
	bool EnableAutoDownloadToPC;


	/// THIS FEATURE IS CURRENTLY NOT IMPLEMENTED!
	/// This value will be ignored by the DLL.
	/// If this is <b>true</b>, then the auto-download frames will be selected by the number of pre-trigger frames and post-trigger frames, not by the start and end frame.
	/// In any mode other than Pre/Post Trigger Mode, this value will be ignored, and always set to false
	bool AutoDownloadByPrePostFrames;

	/// THIS FEATURE IS CURRENTLY NOT IMPLEMENTED!
	/// This value will be ignored by the DLL.
	/// The number of pre-trigger frames to download from camera RAM, for the auto-download process, if AutoDownloadByPrePostFrames is true
	int AutoDownloadPreTriggerFrames;

	/// THIS FEATURE IS CURRENTLY NOT IMPLEMENTED!
	/// This value will be ignored by the DLL.
	/// The number of post-trigger frames to download from camera RAM, for the auto-download process, if AutoDownloadByPrePostFrames is true
	int AutoDownloadPostTriggerFrames;
} StructAutoDownloadSettings;


/// Multi-Speed Settings

/// This struct is used by MS_SetMultiSpeedSettings() to set the capture settings for \ref multispeedtriggermode.\n
/// This struct is also used by MS_GetMultiSpeedSettings() to report the capture settings for \ref multispeedtriggermode.

/// In \ref multispeedtriggermode, the camera can capture at a total of 8 different speed and exposure time settings, and can advance to the next setting by trigger pulse or by frame count\n
/// The arrays in this struct store each of these 8 setting groups

typedef struct _StructMultiSpeedSettings
{
	/// Enable advancing to the next trigger by total frames acquired

	/// If StructMultiSpeedSettings::MultiTriggerEnableByFrames is <b>true</b>, and StructMultiSpeedSettings::MultiTriggerEnableByTrigger is <b>false</b>,
	///  then the camera will advance to the next speed based on the number of frames elapsed, specified by StructMultiSpeedSettings::MultiTriggerFrames.\n
	/// \n
	/// If StructMultiSpeedSettings::MultiTriggerEnableByFrames is <b>false</b>, and StructMultiSpeedSettings::MultiTriggerEnableByTrigger is <b>true</b>,
	///  then the camera will advance to the next speed when the next trigger pulse is received.\n
	/// \n
	/// If StructMultiSpeedSettings::MultiTriggerEnableByFrames and StructMultiSpeedSettings::MultiTriggerEnableByTrigger are both <b>true</b>,
	///  then the camera will act as if StructMultiSpeedSettings::MultiTriggerEnableByFrames is <b>true</b>, and StructMultiSpeedSettings::MultiTriggerEnableByTrigger is <b>false</b>,
	///  meaning that the camera will advance to the next speed based on the number of frames elapsed, specified by StructMultiSpeedSettings::MultiTriggerFrames.\n
	/// \n
	/// If StructMultiSpeedSettings::MultiTriggerEnableByFrames and StructMultiSpeedSettings::MultiTriggerEnableByTrigger are both <b>false</b>,
	///  then the camera will not switch to the next speed, and will continue at the current speed until it reaches the end of camera RAM.\n
	bool MultiTriggerEnableByFrames[8];
	/// see StructMultiSpeedSettings::MultiTriggerEnableByFrames
	bool MultiTriggerEnableByTrigger[8];

	/// The speed to capture at, for each setting group
	long MultiTriggerFPS[8];

	/// The exposure time to capture at, for each setting group
	long MultiTriggerExposureTime[8];

	/// The number of frames to capture at each speed before moving to the next speed.
	long MultiTriggerFrames[8];

	/// The index of the last frame captured at each speed.

	/// These values are updated when the capture is stopped.\n
	long MultiTriggerEndFrameNum[8];

} StructMultiSpeedSettings;


/// Binning Settings

/// This struct is used by MS_SetBinningSettings() to set the camera's \ref binning settings.\n
/// This struct is also used by MS_GetBinningSettings() to report the camera's current \ref binning settings.

/// These values will have no effect on camera models that do not support \ref binning .\n
/// Use the MS_CheckIfCameraHasBinning() function to check if the camera has \ref binning .

typedef struct _StructBinningSettings
{
	/// The \ref binning style that the camera will use.

	/// For a list of allowed values, see \ref binningstyles
	int BinningStyle;

	/// Determines whether pixel summing is enabled.  This value will have no effect if binning is disabled.

	/// For a list of allowed values, see \ref pixelsummingstyles
	int PixelSumming;

} StructBinningSettings;

/// Auto-Exposure Settings

/// This struct is used by MS_SetAutoExposureSettings() to set the camera's auto-exposure settings.\n
/// This struct is also used by MS_GetAutoExposureSettings() to report the camera's current auto-exposure settings.
/// This struct is also used by MS_GetAutoExposureDefaults() to get the default values for the current image size and frame rate.

/// These values will have no effect on camera models that do not support auto-exposure .\n
/// Use the MS_CheckIfCameraHasAutoExposure() function to check if the camera has auto-exposure .

typedef struct _StructAutoExposureSettings
{
	/// If this is set to <b>true</b>, then the camera will use auto-exposure when capturing.\n
	/// If this is set to <b>false</b>, then the camera will not use auto-exposure when capturing\n
    bool EnableAutoExposure;

    /// The Auto-Exposure Target Value is the target pixel value for the auto-exposure feature.  The camera will try to adjust the camera's exposure time so that the average pixel value in the target window is as close to this value as possible.  Simply start a continuous capture and adjust this value until the image is at the desired level of brightness.
	int TargetValue;

	/// The Auto-Exposure Error Margin is used to control how precisely the camera will try to match the target pixel value.  For example, at a value of 2%, the camera will adjust the camera's exposure time until the average pixel value in the target window is within 2% of the target pixel value.  A lower value will attempt to match the exposure time more precisely, but will cause the exposure time to update more frequently.  A higher value will cause the exposure time to change less often, but will not match the target value as precisely.  The default value of 2 will give good results for almost any situation, and should not be changed unless you want more precise control over how often the exposure time changes.
	int ErrorMargin;

	/// The Minimum Auto-Exposure Time is used to set a limit to how low the camera will automatically adjust the exposure time.  The default value is 1.  If the exposure time reaches this limit, and the image still isn't bright enough, then you will need to increase this value.
	int MinExposureTime;

	/// The Maximum Auto-Exposure Time is used to set a limit to how high the camera will automatically adjust the exposure time.  The default value is 500.  If the exposure time reaches this limit, and the image still isn't bright enough, then you will need to increase this value.
	int MaxExposureTime;

    /// The Auto-Exposure Window Width is simply the width of the auto-exposure window.  As you adjust this value, you will see the green box in the capture window change its width.
	int WindowWidth;

	/// The Auto-Exposure Window Height is simply the height of the auto-exposure window.  As you adjust this value, you will see the green box in the capture window change its height.
    int WindowHeight;

	/// The Auto-Exposure Target location X is simply the X-coordinate of the auto-exposure window.  As you adjust this value, you will see the green box in the capture window move left or right.  This has the same effect as simply clicking and dragging the green rectangle in the capture window.
	int TargetLocationX;

	/// The Auto-Exposure Target location Y is simply the Y-coordinate of the auto-exposure window.  As you adjust this value, you will see the green box in the capture window move up or down.  This has the same effect as simply clicking and dragging the green rectangle in the capture window.
	int TargetLocationY;

} StructAutoExposureSettings;

/*!
@}
*/

/*! \defgroup camerastatusstructs Camera Status Structs

These structs are used to read the camera's status.

The following structs are in this category:\n
\n
\ref ::StructCameraStatus
\n
\ref ::StructCaptureStatus
\n
\ref ::StructCurrentImageSize
\n
\ref ::StructCameraTemperature
\n
\ref ::StructPreviewStatus
\n
\ref ::StructDownloadStatus
\n
\ref ::StructFileStatus
\n
\ref ::StructBufferStatus
\n
\ref ::StructGigabitConnectionStatus
\n


@{
*/

/// Camera Status

/// This struct is used by MS_GetCameraStatus(), to report the camera's current mode.

/// There is no MS_SetCameraStatus() function.\n
/// \copydoc functionstoswitchcameramodes

typedef struct _StructCameraStatus
{
	/// The mode that the camera will be in, the next time it receives a start command.

	/// \attention This value does not report the camera's current state.  It reports the state that the camera will be in when it receives the start command.\n
	/// This means that this value will never be set to ::c_CameraModeStop or ::c_CameraModePauseDownloadToPC.\n
	///
	/// The camera's current state is reported by StructCameraStatus.CameraCurrentState.\n
	/// \n
	/// For a list of allowed values, see \ref cameramodenumbers\n
	int CameraMode;

	/// The type of trigger that the camera will wait for, if StructCameraStatus::CameraMode is set to ::c_CameraModeStartStopByTriggerToCameraRAM.

	/// For a list of allowed values, see \ref triggertypenumbers\n
	int TriggerType;

	/// The camera's current state.

	/// \attention If the camera stops automatically, then there may be a delay of up to 1 second before this value is updated to ::c_CameraModeStop.\n
	///
	/// For a list of allowed values, see \ref cameramodenumbers\n
	int CameraCurrentState;

} StructCameraStatus;


/// Capture Status

/// This struct is used by MS_GetCaptureStatus(), to get the status of a capture that is currently in progress.

/// These values are updated approximately 2 to 4 times per second.

typedef struct _StructCaptureStatus
{
	/// Camera is Capturing or Downloading

	/// This will be <b>true</b> if the camera is currently capturing to camera RAM or downloading from camera RAM.\n
	/// This will also be <b>true</b> if the camera is armed, and waiting for a trigger pulse, but not capturing to camera RAM yet.\n
	/// This will also be <b>true</b> if the camera is currently paused, in the middle of a download from camera RAM.\n
	/// This will be <b>false</b> if the camera is in \ref stopmode, or in \ref downloadpreviewmode.\n
	bool IsCapturingOrDownloading;

	/// The total number of frames that have been captured by the camera since the current capture was started.

	long TotalFramesCapturedByCamera;

	/// The frame that is currently being written to, in camera RAM.

	/// In \ref continuousmode, if the capture reaches the end of camera RAM, the camera will go back to position 0, and overwrite the previous contents of camera RAM.\n
	long CurrentFrameInCameraRAM;

	/// Camera is Armed

	/// In \ref breakboardtriggermode, this will be <b>false</b> if the camera is currently waiting for the trigger line to be held high for one second before entering the armed state,
	///  or <b>true</b> if the camera has already entered the armed state.\n
	/// In \ref switchclosuretriggermode, this will be <b>false</b> if the camera is currently waiting for the trigger line to be held low for one second before entering the armed state,
	///  or <b>true</b> if the camera has already entered the armed state.\n
	/// In any of the other \ref cameramodes , this will always be <b>true</b>.\n
	bool CameraIsArmed;

	/// Camera is Waiting for Trigger

	/// In \ref continuousmode or \ref slavetriggermode, this will be <b>true</b> if a capture is in progress, or <b>false</b> if a capture is not in progress.\n
	/// In any other \ref triggermode, this will be <b>true</b> if the camera is armed and waiting for a trigger pulse,
	///  or <b>false</b> if the camera is capturing to camera RAM.\n
	/// This will always be <b>false</b> if a capture is not in progress.\n
	bool WaitingForTrigger;

	/// Camera is Doing \ref precapture

	/// When the camera is in \ref triggermode, it needs to do a brief \ref precapture before arming the camera.\n
	/// The \ref precapture lasts less than 1 second.\n
	/// This value will be <b>true</b> while the \ref precapture is in progress, and <b>false</b> at any other time.\n
	bool DoingPreCapture;

	/// The frame number that the previous capture stopped at.

	/// This value is updated each time the capture is stopped.\n
	/// The DLL also saves this value to the \ref previoussettingsfile, and loads this value each you reconnect to the camera.\n
	long LastCaptureStopPos;

} StructCaptureStatus;


/// Current Image Size

/// This struct is used by MS_GetCurrentImageSize() to report the camera's current image size settings.

/// There is no MS_SetCurrentImageSize() function.  To change the current image size, use the MS_ChangeImageSize() function.\n
/// \attention Make sure you don't confuse the size of the image stored in the camera with the size of the preview image sent back from the camera.\n
///             This could result in the image being displayed incorrectly, or it could result in trying to access memory that is out of bounds.

typedef struct _StructCurrentImageSize
{
	/// The width and height of the images that the camera will store in its internal RAM when the next capture starts, before \ref binning is applied.

	/// \copydoc functionsthatuseimagesizebeforebinning
	int ImageWidthInCameraBeforeBinning;

	/// see StructCurrentImageSize::ImageWidthInCameraBeforeBinning
	int ImageHeightInCameraBeforeBinning;

	/// The width and height of the images that the camera will store in its internal RAM when the next capture starts, after \ref binning is applied.

	/// \copydoc functionsthatuseimagesizeafterbinning
	int ImageWidthInCameraAfterBinning;

	/// see StructCurrentImageSize::ImageWidthInCameraAfterBinning
	int ImageHeightInCameraAfterBinning;

	/// The width and height of the images that the camera will send to the PC.

	/// \copydoc functionsthatuseimagesizefromcamera
	int ImageWidthFromCamera;

	/// see StructCurrentImageSize::ImageWidthFromCamera
	int ImageHeightFromCamera;

	/// Image Size Was Reduced

	/// This will be <b>true</b> if the preview image size was reduced, in order for the preview image to fit in the camera's buffer.\n
	/// This will be <b>false</b> if the preview image size did not need to be reduced.\n
	/// \n
	/// See \ref functionsthatuseimagesizefromcamera
	bool ImageSizeWasReduced;

	/// Finished Changing image Size

	/// This value will be <b>false</b> while the MS_ChangeImageSize() function is running, and <b>true</b> at any other time.\n
	bool FinishedChangeImageSize;

} StructCurrentImageSize;


/// Camera Temperature

/// This struct is used by MS_GetCameraTemperature() to report the camera's current temperature status.

/// If the camera's core temperature reaches the shutdown temperature, then the camera will enter \ref autoshutdownmode mode, and not respond to any commands until it cools down below the shutdown temperature.\n
/// These values are updated approximately once per second.

typedef struct _StructCameraTemperature
{
	/// These values report the camera's current core temperature and current board temperature, in degrees Celsius.

	/// The formula for converting to degrees Celsius is:\n
	/// Fahrenheit = ( 1.8 * Celsius + 32 );\n
	long CoreTemperature;

	/// see StructCameraTemperature::CoreTemperature
	long BoardTemperature;

	/// This will be <b>true</b> if the camera is currently in \ref autoshutdownmode, and will be <b>false</b> at any other time.
	bool CameraIsAutoShutdown;

	/// This will be <b>true</b> if the camera has entered \ref autoshutdownmode mode since the time the last capture was started, and will be <b>false</b> at any other time.
	bool CameraWasAutoShutdown;

	/// Reports the temperature at which the camera will enter \ref autoshutdownmode mode, in degrees Celsius.
	long shutdownTemperature;

} StructCameraTemperature;


/// Preview Status

/// This struct is used by MS_GetPreviewStatus() to report the camera's current preview status.

/// There is no MS_SetPreviewStatus() function.  To set the next preview frame to display, use the MS_SetUpdatePreviewPicPos() function.\n
/// \n
/// These values will only be valid when the StructCameraStatus::CameraMode is ::c_CameraModeDownloadToPC, and a download is not currently in progress.\n
/// \n
/// Use the function MS_SwitchToDownloadToPCMode() to set the camera to \ref downloadtopcmode.\n
/// Use the function MS_ExitDownloadModeAndReturnToPreviousCaptureMode() to exit \ref downloadtopcmode, and return to the previous capture mode.\n
/// Use the function MS_StartPreview() to start displaying the download preview frames.\n
/// Use the function MS_StopPreview() to stop displaying download preview frames.

typedef struct _StructPreviewStatus
{
	/// This will be <b>true</b> if the camera is currently sending download preview frames, and will be <b>false</b> at any other time.
	bool IsInPicturePreview;

	/// The frame number of the last preview frame that was sent from the camera.  If no preview frames have been sent yet, this will be -1.
	int UpdatePreviewPicPosAtLastPreviewUpdate;

	/// The frame number of the next preview frame that you want the camera to send.

	/// Use the MS_SetUpdatePreviewPicPos() function to set this value.\n
	/// If you have not requested a specific frame yet, then this will be 0.\n
	int UpdatePreviewPicPos;

} StructPreviewStatus;


/// Download Status

/// This struct is used by MS_GetDownloadStatus() to report the camera's current download status.

/// These values are updated immediately, whenever a new frame is received.

typedef struct _StructDownloadStatus
{
	/// Frames Saved To Hard Drive

	/// The number of frames that have been saved to the PC's hard drive, when downloading to an AVI file, or to a series of bitmaps or jpegs.\n
	/// If you are downloading to PC RAM only, then this will always be 0.\n
	unsigned long FramesSavedToHardDrive;

	/// Download Is Paused

	/// This will be <b>true</b> if the download is currently paused using the MS_PauseDownload() function, and will be <b>false</b> at any other time.\n
	bool DownloadIsPaused;

	/// Is Processing Overload

	/// This will be <b>true</b> if the camera has stopped sending frames to the PC (because it was sent the stop command), but the PC is still saving frames from the buffer in PC RAM to an AVI file.\n
	/// This will be <b>false</b> at any other time.\n
	bool IsProcessingOverload;

	/// Gigabit Overload

	/// This is the number of frames in the PC's gigabit buffer that haven't been processed yet.\n
	/// If this number exceeds StructDownloadStatus::GigabitOverloadLimit, then the download will fail.\n
	/// The DLL will attempt to automatically reduce the download speed if StructDownloadStatus::GigabitOverload increases past half of StructDownloadStatus::GigabitOverloadLimit.\n
	long GigabitOverload;

	/// The highest value that StructDownloadStatus::GigabitOverload has reached since the current download was started
	long HighestGigabitOverloadSinceDownloadStart;

	/// The size of the PC's gigabit buffer.  If StructDownloadStatus::GigabitOverload exceeds this value, then the download will fail.
	long GigabitOverloadLimit;

	/// Failed To Keep Up With Gigabit

	/// This will be <b>true</b> if StructDownloadStatus::GigabitOverload has exceeded StructDownloadStatus::GigabitOverloadLimit during this download, and the download has failed.\n
	/// This will be <b>false</b> at any other time.\n
	bool FailedToKeepUpWithGigabit;

	/// The number of frames in the PC's hard drive buffer that haven't been processed yet.

	/// If this number exceeds StructDownloadStatus::HardDriveOverloadLimit, then the download will fail.\n
	/// The DLL will attempt to automatically reduce the download speed if StructDownloadStatus::HardDriveOverload increases past half of StructDownloadStatus::HardDriveOverloadLimit.\n
	long HardDriveOverload;

	/// The highest value that StructDownloadStatus::HardDriveOverload has reached since the current download was started
	long HighestHardDriveOverloadSinceDownloadStart;

	/// This is the size of the PC's hard drive buffer.  If StructDownloadStatus::HardDriveOverload exceeds this value, then the download will fail.

	/// This is actually the same value as StructBufferStatus::ImageBufferCount, since the StructBufferStatus::ImageBuffers are used to buffer the data as it is being saved to the hard drive.\n
	long HardDriveOverloadLimit;

	/// Failed To Keep Up With Hard Drive

	/// This will be <b>true</b> if StructDownloadStatus::HardDriveOverload has exceeded StructDownloadStatus::HardDriveOverloadLimit during this download, and the download has failed.\n
	/// This will be <b>false</b> at any other time.\n
	bool FailedToKeepUpWithHardDrive;

	/// Is Doing Auto-Download To Flash

	/// This will be <b>true</b> if the camera is currently doing an automatic download to the camera's internal Flash RAM (in camera models that have internal Flash RAM).\n
	/// The auto-download to Flash will happen after a capture stops, if EnableAutoDownloadToFlash is set to <b>true</b>.\n
	/// The auto-download to Flash will only happen in \ref singlesequencetriggermode, \ref breakboardtriggermode,  \ref switchclosuretriggermode, or  \ref multispeedtriggermode \n
	/// The auto-download to Flash will only happen in camera models that have internal Flash RAM \n
	bool IsDoingAutoDownloadToFlash;

	/// The total number of frames to download.  This is determined by StructDownloadSettings::DownloadStartPos and StructDownloadSettings::DownloadEndPos
	long FramesToDownload;

} StructDownloadStatus;


/// File Status

/// This struct is used by MS_GetFileStatus() to report the camera's current file writing status.

/// These values are updated immediately, whenever a new frame is saved.

typedef struct _StructFileStatus
{
	/// The current size of the AVI file being written to, in bytes
	unsigned __int64 CurrentAVIFileSize;

	/// In Save Overload Process

	/// This will be <b>true</b> if the camera has stopped sending frames to the PC (because it was sent the stop command), but the PC is still saving frames from the buffer in PC RAM to the hard drive.\n
	/// This is basicly the same as StructDownloadStatus.IsProcessingOverload, except that it also works when saving to BMP and JPG files.\n
	/// This will be <b>false</b> at any other time.\n
	bool InSaveOverloadProcess;

	/// In Save to File Process

	/// This will be <b>true</b> while a save process started by MS_SaveToAVI() or MS_SaveToImageFile() is in progress, and will be <b>false</b> at any other time.\n
	bool InSaveToFileProcess;

	/// The file name of the AVI file that is currently being saved to.  It will be immediately updated if the DLL automatically starts saving to a different file.
	std::string AVISAVENewName;

	/// The file name of the BMP file that is currently being saved to.  It will be immediately updated if the DLL automatically starts saving to a different file.
	std::string BMPSAVENewName;

	/// The file name of the JPG file that is currently being saved to.  It will be immediately updated if the DLL automatically starts saving to a different file.
	std::string JPGSAVENewName;

	/// Finished Saving AVI

	/// This will be <b>true</b> if the DLL has finished saving to an AVI file, and has not started any other capture, download, or save process yet, and will be <b>false</b> at any other time.\n
	bool FinishedSavingAVI;

	/// Finished Saving Compressed AVI

	/// This will be <b>true</b> if the DLL has finished saving to a compressed AVI file, and has not started any other capture, download, or save process yet, and will be <b>false</b> at any other time.\n
	bool FinishedSavingCompressedAVI;

	/// Finished Saving BMP

	/// This will be <b>true</b> if the DLL has finished saving to a series of BMP files, and has not started any other capture, download, or save process yet, and will be <b>false</b> at any other time.\n
	bool FinishedSavingBMP;

	/// Finished Saving JPG

	/// This will be <b>true</b> if the DLL has finished saving to a series of JPG files, and has not started any other capture, download, or save process yet, and will be <b>false</b> at any other time.\n
	bool FinishedSavingJPG;

} StructFileStatus;


/// Buffer Status

/// This struct is used by MS_GetBufferStatus() to report the PC's current image buffer status.

/// These values are updated immediately, whenever any of the values are changed.\n
/// \n
/// Each image buffer stores one frame, in raw format, exactly as it was sent from the camera.\n
/// \n
/// Each pixel is 1 byte.\n
/// \n
/// For a color camera, to convert the image from 8-bit raw data to 32-bit color, use the function MS_GetColorImage()\n
/// For a color camera, to leave the image in 8-bit grayscale format, but remove the bayer pattern noise from the image, use the function MS_GetGrayscaleImage()\n
/// For a black and white camera, to apply the gamma settings to the image, (which leaves the image in 8-bit grayscale format), use the function MS_ApplyGamma()\n
/// \n
/// You can also use the following functions to convert the image to the desired format, and also apply the overlay to the image:\n
/// MS_DoPostProcessingBW()\n
/// MS_DoPostProcessingColor()\n
/// MS_DoPostProcessingGrayscale()\n
/// \n
/// The buffers are reallocated every time the image size changes, or the capture mode changes, or the function MS_SetAllocatedMemorySize() is called.\n
/// \n
/// If your application needs to know when the buffers are reallocated, you can set up a callback function by using MS_SetCallback_ChangingImageSize()\n
/// \attention Do not attempt to manually reallocate the image buffers!  This will cause the DLL to crash!  The DLL will allocate the buffers automatically.\n
///
/// You can use the MS_SetAllocatedMemorySize() function to specify how much RAM you want to use for the image buffers.

typedef struct _StructBufferStatus
{
	/// The number of image buffers that are curerently allocated.
	long ImageBufferCount;

	/// A pointer to the image buffers.

	/// The size of each buffer is (StructCurrentImageSize.ImageWidthFromCamera * (StructCurrentImageSize.ImageHeightFromCamera+1))\n
	/// \attention The extra row at the end of the image data is used by the camera's internal functions, and must not be modified by your software.\n
	/// This extra row will also be saved to AVI files.\n
	/// If you attempt to access the StructBufferStatus::ImageBuffers while changing the image size, the software may crash!\n
	/// Changing the capture mode will automatically change the image size.\n
	unsigned char **ImageBuffers;

	/// The index of the last frame in the buffer that has been written to, when receiving images from the camera.

	/// This value will be updated whenever the DLL finishes saving a frame from the camera into the buffer.\n
	/// The frame stored at this index can safely be read by your application, but the frame immediately after it is currently being written to by the DLL, if a capture or download is in progress.\n
	int LastValidFrame;

	/// The total number of frames that have been saved to the image buffers, since the current capture or download was started.
	long TotalFramesSavedToBuffer;

	/// The number of megabytes that have been reserved for the image buffers.

	/// You can adjust this value by using the MS_SetAllocatedMemorySize() function.\n
	/// The total amount of RAM used by the DLL will be slightly more than this value, since the image buffers aren't the only thing the DLL needs to reserve memory for.\n
	float ImageBufferSizeInMegabytes;

} StructBufferStatus;


/// Gigabit Connection Status

/// This struct is used by MS_GetGigabitConnectionStatus() to report the camera's gigabit connection status.

/// These values are updated approximately once per second.

typedef struct _StructGigabitConnectionStatus
{
	/// Camera Is Connected

	/// This will be <b>true</b> if the DLL is currently connected to the camera, and will be <b>false</b> at any other time.\n
	bool CameraIsConnected;

	/// Is Selecting Camera

	/// This will be <b>true</b> if the "camera select" dialog is open, and will be <b>false</b> at any other time.\n
	bool IsSelectingCamera;

	/// Is Connecting to Camera

	/// This will be <b>true</b> if the DLL is currently in the process of connecting to the camera, and will be <b>false</b> at any other time.\n
	bool IsConnectingToCamera;

	/// Camera Was Connected

	/// This will be <b>true</b> if the DLL has successfully connected to the camera at least once since the DLL was started.\n
	/// This will be <b>false</b> if the DLL has not successfully connected to the camera yet, since the DLL was started.\n
	bool WasConnected;

	/// The MAC address of the last camera that the DLL has connected to.
	std::string LastDeviceMAC;

	/// The IP address of the last camera that the DLL has connected to.
	std::string LastDeviceIP;

	/// The name of the last camera that the DLL has connected to.
	std::string LastDeviceName;

	/// The connection mode that was used the last time that the DLL connected to the camera.

	/// For a list of allowed values, see \ref drivertypes
	int LastConnectedMode;

	/// The MAC address of the camera that the DLL is currently connected to.
	char CurrentMacAddress[18];

} StructGigabitConnectionStatus;


/*!
@}
*/

/*! \defgroup limitstruct Camera Limit Structs

These structs contain information about limits of various operating parameters of the camera.

The following structs are in this category:\n
\ref ::AutoExposureLimits
\n

@{
*/

/// Range (Integer)
typedef struct _RangeInt
{
/// The minimum value.
	int Min;
/// The maximum value.
	int Max;
} RangeInt;

/// Auto Exposure Limits
/// This struct is used by ::MS_GetAutoExposureLimits()

typedef struct _AutoExposureLimits
{
/// The minimum and maximum allowed values for the auto-exposure target value.
	RangeInt TargetValue;
///  The minimum and maximum allowed values for the auto-exposure error margin.	
	RangeInt ErrorMargin;
///  The minimum and maximum allowed values for the auto-exposure minimum exposure time.	
	RangeInt MinExposure;
///  The minimum and maximum allowed values for the auto-exposure maximum exposure time.	
	RangeInt MaxExposure;
///  The minimum and maximum allowed values for the auto-exposure window width.	
	RangeInt WindowWidth;
///  The minimum and maximum allowed values for the auto-exposure window height.	
	RangeInt WindowHeight;
} AutoExposureLimits;


/*!
@}
*/


/*! \defgroup otherstructs Other Structs

These structs are used only by specific functions in this DLL, for purposes other than reading or writing the camera's settings or status.

The following structs are in this category:\n
\n
\ref ::StructPresetSettings
\n
\ref ::StructDataFromAVIFile
\n

@{
*/





/// Preset Settings

/// This struct is used only by the callback function \ref MS_SetCallback_CheckPresetSettings() "Callback_CheckPresetSettings()", to confirm that you want to load the most recently used capture settings, when the DLL is loaded.

typedef struct _StructPresetSettings
{
	/// These are the width and height of the images that the camera will store in its internal RAM when the next capture starts.
	int ImageWidth;
	/// see StructPresetSettings::ImageWidth
	int ImageHeight;

	/// The camera's capture speed, in frames per second.
	int Speed;

	/// The camera's exposure time, in microseconds.
	int ExposureTime;

	/// The camera's gain value.
	int Gain;

	/// The camera's black offset value.
	int BlackOffset;

	/// The camera's boost value.  This value is only used for MS70K and MS75K cameras.
	int Boost;

	/// The mode that the camera will be in, the next time it receives a start command.

	/// For a list of allowed values, see \ref cameramodenumbers
	int CameraMode;

	/// The type of trigger that the camera will wait for, if the camera is in \ref triggermode.

	/// For a list of allowed values, see \ref triggertypenumbers
	int TriggerType;

	/// Used internally by the DLL.  Changing this value will have no effect.
	bool DataIsValid;

} StructPresetSettings;


/// Data From AVI File

/// This struct is used by MS_ReadAVIFileData() to read the AVI file's embedded data.

typedef struct _StructDataFromAVIFile
{
	long totalFrames                  ; ///<   1 - the number of frames in the AVI file
	long imageWidth                   ; ///<   2 - the image width
	long imageHeight                  ; ///<   3 - the image height
	long captureSpeed                 ; ///<   6 - the capture speed, in FPS
	double fileSize                   ; ///<   8 - the size of the AVI file, in megabytes
	SYSTEMTIME downloadDate           ; ///<   9 - the date the AVI file was downloaded from the camera

	double softwareCodeVersion        ; ///< 118 - software code version
	double cameraCodeVersion          ; ///< 119 - camera code version

	int CameraMode                    ; ///< 121 - camera mode
	int triggerType                   ; ///< 122 - trigger type
	long exposureTime                 ; ///< 123 - exposure time
	long gainValue                    ; ///< 126 - gain value
	long boostLevel                   ; ///< 129 - boost level (70K and 75K only)

	int displayMode                   ; ///< 130 - display mode
	int bayerRed                      ; ///< 131 - bayer red
	int bayerGreen                    ; ///< 132 - bayer green
	int bayerBlue                     ; ///< 133 - bayer blue
	double bayerGamma                 ; ///< 134 - bayer gamma

	int VerticalReticleX              ; ///< 140 - vertical reticle X
	int VerticalReticleColor          ; ///< 141 - vertical reticle color
	int CrosshairReticleX             ; ///< 142 - crosshair reticle X
	int CrosshairReticleY             ; ///< 143 - crosshair reticle Y
	int CrosshairReticleColor         ; ///< 144 - crosshair reticle color
	int CrosshairReticleWidth         ; ///< 145 - crosshair reticle width
	int CrosshairReticleHeight        ; ///< 146 - crosshair reticle height
	int CrosshairReticleWidthType     ; ///< 147 - crosshair reticle width type
	int CrosshairReticleHeightType    ; ///< 148 - crosshair reticle height type

	int bayerWhite                    ; ///< 156 - bayer white (intensity)
	double bayerRawGamma              ; ///< 157 - bayer raw gamma ( for intensity )

	int encodedDataRows               ; ///< 171 - encoded data rows
	int RS422DataBytes                ; ///< 177 - RS422 data bytes

    bool EnableAutoExposure           ; ///< 178 - EnableAutoExposure;

    int AutoExposureTargetValue       ; ///< 179 - AutoExposureTargetValue;
    int AutoExposureErrorMargin       ; ///< 180 - AutoExposureErrorMargin;
    int AutoExposureMinExposureTime   ; ///< 181 - AutoExposureMinExposureTime;
    int AutoExposureMaxExposureTime   ; ///< 182 - AutoExposureMaxExposureTime;

    int AutoExposureWindowWidth       ; ///< 183 - AutoExposureWindowWidth;
    int AutoExposureWindowHeight      ; ///< 184 - AutoExposureWindowHeight;
    int AutoExposureTargetLocationX   ; ///< 185 - AutoExposureTargetLocationX;
    int AutoExposureTargetLocationY   ; ///< 186 - AutoExposureTargetLocationY;

	bool AutoExposureIsHighSensitivity; ///< 187 - AutoExposureIsHighSensitivity;

	std::string cameraType            ; ///< 199 - the camera type

} StructDataFromAVIFile;

/*!
@}
*/

/*!
@}
*/

/***************************************************************************************************************************************/

/*! \defgroup cameraconstants Camera Constants

These are the constants used by the DLL.

These constants are divided into the following categories:\n
\n
\ref cameramodenumbers
\n
\ref triggertypenumbers
\n
\ref downloaddestinationtypes
\n
\ref colormodes
\n
\ref overlaytypes
\n
\ref imagefiletypes
\n
\ref drivertypes
\n
\ref binningstyles
\n
\ref pixelsummingstyles
\n
\ref rs422bytevalues
\n
\ref packettypes
\n
\ref timestampdisplaymodes
\n
\ref boostvalues
\n
\ref statuscodes
\n

@{
*/







/*!
\defgroup cameramodenumbers Camera Mode Numbers

These are the allowed values for StructCameraStatus.CameraMode and StructCameraStatus.CameraCurrentState
@{
*/
/// \ref stopmode

/// In this mode, the camera is idle.\n
/// \n
///   See \ref stopmode for more information.
const int c_CameraModeStop                          =  0;
/// \ref downloadtopcmode

/// In this mode, the camera will download frames from camera RAM to the PC.\n
/// \n
///   See \ref downloadtopcmode for more information.
const int c_CameraModeDownloadToPC                  =  1;
/// \ref continuousmode

/// In this mode, the camera will continuously capture to camera RAM.\n
/// \n
///   See \ref continuousmode for more information.
const int c_CameraModeContinuousCaptureToCameraRAM  =  2;
/// \ref triggermode

/// In this mode, the camera will start and stop when it receives a trigger pulse.\n
///   StructCameraStatus.TriggerType will determine how it responds to each trigger pulse.\n
/// \n
///   See \ref triggermode for more information.
const int c_CameraModeStartStopByTriggerToCameraRAM =  4;
/// \ref pausedownloadmode

/// In this mode, the camera will pause downloading from camera RAM to the PC, and will resume when it is sent the command to resume.\n
/// \n
///   See \ref pausedownloadmode for more information.
const int c_CameraModePauseDownloadToPC             =  7;
/// \ref clearcamerarammode

/// In this mode, the camera is clearing the contents of its internal RAM.\n
/// \n
///   See \ref clearcamerarammode for more information.
const int c_CameraModeClearCameraRAM                =  8;
/*!
@}
*/



/*!
\defgroup triggertypenumbers Trigger Type Numbers

These are the allowed values for StructCameraStatus.TriggerType
@{
*/
/// \ref singlestartstoptriggermode
/// In this mode, the first trigger pulse will start the camera.\n
///   The second trigger pulse will stop the camera and end the capture.\n
/// \n
///   See \ref singlestartstoptriggermode for more information.
const int c_TriggerTypeSingleStartStop   = 0;

/// \ref multiplestartstoptriggermode
/// In this mode, the first trigger pulse will start the camera.\n
///   The second trigger pulse will stop the camera.\n
///   After each stop pulse, the camera will return to waiting for another start pulse.\n
/// \n
///   See \ref multiplestartstoptriggermode for more information.
const int c_TriggerTypeMultipleStartStop = 1;

/// \ref singlesequencetriggermode
/// In this mode, the first trigger pulse will start the camera.\n
///   When the camera's RAM is filled, the camera will stop and the capture will end.\n
/// \n
///   See \ref singlesequencetriggermode for more information.
const int c_TriggerTypeSingleSequence    = 2;

/// \ref breakboardtriggermode
/// In this mode, the trigger line must be held high for 1 second to arm the camera.\n
///   After the camera is armed, when the breakboard is broken, the camera will start capturing.\n
///   When the camera's RAM is filled, the camera will stop and the capture will end.\n
/// \n
///   See \ref breakboardtriggermode for more information.
const int c_TriggerTypeBreakboard        = 3;

/// \ref switchclosuretriggermode
/// In this mode, the trigger line must be held low for 1 second to arm the camera.\n
///   After the camera is armed, when the switch is closed, the camera will start capturing.\n
///   When the camera's RAM is filled, the camera will stop and the capture will end.\n
/// \n
///   See \ref switchclosuretriggermode for more information.
const int c_TriggerTypeSwitchClosure     = 4;

/// \ref slavetriggermode
/// In this mode, the camera will remain idle while the trigger line is held low.\n
///   The camera will start exposing when the trigger line goes high.\n
///   The camera will stop exposing and go idle again when the trigger goes low.\n
/// \n
///   See \ref slavetriggermode for more information.
const int c_TriggerTypeSlave             = 5;

/// \ref multispeedtriggermode
/// In this mode, the camera will capture at a series of up to 8 different speeds and exposure times, as configured in ::StructMultiSpeedSettings.\n
/// \n
///   See \ref multispeedtriggermode for more information.
const int c_TriggerTypeMultiSpeed        = 6;

/// \ref activetriggermode
/// In this mode, the camera will capture while the trigger line is held high, and will be idle when the trigger line is held low.\n
/// \n
///   See \ref activetriggermode for more information.
const int c_TriggerTypeActive            = 7;

/// \ref preposttriggermode
/// In this mode, the camera will capture continuously until a trigger pulse is received, then it will capture a specified number of frames.\n
/// \n
///   See \ref preposttriggermode for more information.
const int c_TriggerTypePrePost           = 9;

/// \ref singlesequencewithpreviewmode
/// In this mode, the first trigger pulse will start the camera.\n
///   When the camera's RAM is filled, the camera will stop and the capture will end.\n
///   The camera will send preview frames even when the camera is not saving frames to RAM.\n
/// \n
///   See \ref singlesequencewithpreviewmode for more information.
const int c_TriggerTypeSingleSequenceWithPreview    = 10;
/*!
@}
*/



/*!
\defgroup downloaddestinationtypes Download Destination Types

These are the allowed values for StructDownloadSettings.DestFileType
@{
*/
/// Download To PC RAM

/// In this mode, the frames will be stored in PC RAM, but will not be saved to a file.
const int c_DownloadToRAM           = 0;
/// Download To BMP Files

/// In this mode, the frames will be stored in PC RAM, and saved to a series of BMP files.
const int c_DownloadToBMP           = 1;
/// Download To JPG Files

/// In this mode, the frames will be stored in PC RAM, and saved to a series of JPG files.
const int c_DownloadToJPG           = 2;
/// Download To AVI File

/// In this mode, the frames will be stored in PC RAM, and saved to an uncompressed AVI file.
const int c_DownloadToAVI           = 3;
/// Download To Compressed AVI File

/// In this mode, the frames will be stored in PC RAM, and saved to a compressed AVI file.
const int c_DownloadToCompressedAVI = 4;
/// Download To Compressed AVI File

/// This is exactly the same as ::c_DownloadToCompressedAVI, but has a shorter name.
const int c_DownloadToCOM           = 4;
/*!
@}
*/



/*!
\defgroup colormodes Color Modes

These are the allowed values for StructColorSettings.DisplayMode
@{
*/
/// Color Mode

/// In this mode, the images will be saved in 32-bit color, after applying the bayer algorithm.  This mode should only be used with a color camera.
const int c_ColorModeColor     = 1;
/// Black And White Mode

/// In this mode, the images will be saved in 8-bit grayscale, in the raw format sent by the camera.  This mode should only be used with a black and white camera.
const int c_ColorModeBW        = 2;
/// Grayscale Mode

/// In this mode, the images will be saved in 8-bit grayscale, after applying the bayer algorithm to remove the bayer pattern noise.  This mode should only be used with a color camera.
const int c_ColorModeGrayscale = 6;
/// Gamma Mode

/// In this mode, the images will be saved in 8-bit grayscale, after applying the gamma algorithm to brighten the picture.  This mode should only be used with a black and white camera.
const int c_ColorModeGamma     = 7;
/*!
@}
*/





/*!
\defgroup overlaytypes Overlay Types

These are the allowed values for StructOverlaySettings.OverlayChoiceTopLeft, OverlayChoiceTopRight, OverlayChoiceBottomLeft, and OverlayChoiceBottomRight
@{
*/
/// None

/// This will disable the overlay for this slot.
const int c_OverlayChoiceNone             = 0;
/// Marker

/// This will display the frame marker in this slot.
const int c_OverlayChoiceMarker           = 1;
/// Gigabit Time Stamp

/// This is not implemented in this version of the DLL.
const int c_OverlayChoiceGigabitTimeStamp = 2;
/// IRIG Time Stamp

/// This will display the IRIG-format timestamp in this slot.
const int c_OverlayChoiceIRIGTimeStamp    = 3;
/// Capture Start Date

/// This is not implemented in this version of the DLL.
const int c_OverlayChoiceCaptureStartDate = 4;
/// Capture Speed

/// This will display the capture speed in this slot.
const int c_OverlayChoiceCaptureSpeed     = 5;
/// Exposure Time

/// This will display the exposure time in this slot.
const int c_OverlayChoiceExposureTime     = 6;
/// Custom Data 1

/// This will display custom string 1 in this slot.
const int c_OverlayChoiceCustom1          = 7;
/// Custom Data 2

/// This will display custom string 2 in this slot.
const int c_OverlayChoiceCustom2          = 8;
/// AtoD Data

/// This will display the camera's AtoD Data in this slot.
const int c_OverlayChoiceAtoDData         = 9;
/// RS422 Data

/// This will display the camera's RS422 Data in this slot.
const int c_OverlayChoiceRS422Data        = 10;
/*!
@}
*/



/*!
\defgroup imagefiletypes Image File Types

These are the allowed values for StructImageFileSettings.ImageFileType
@{
*/
/// BMP

/// This will save to a series of BMP files.
const int c_ImageTypeBMP = 0;
/// JPG

/// This will save to a series of JPG files.
const int c_ImageTypeJPG = 1;
/// TIF

/// This will save to a series of TIF files.
const int c_ImageTypeTIF = 2;
/*!
@}
*/



/*!
\defgroup drivertypes Driver Types

These are the allowed values for StructGigabitConnectionStatus.LastConnectedMode
@{
*/
/// None

/// This indicates that the camera has not been connected yet.
const int c_ConnectionModeNone = -1;
/// High Performance Driver

/// This indicates that the camera was connected through the high-performance driver.  This is the best mode, and should be used whenever connecting from a PC that has the high performance driver installed.
const int c_ConnectionModeHighPerformance = 0;
/// Filter Driver

/// This indicates that the camera was connected through the Filter driver.  This is the second-best mode, and should be used whenever connecting from a PC that does not have the high performance driver installed..
const int c_ConnectionModeFilterDriver    = 1;
/// Windows Driver

/// This indicates that the camera was connected through the standard Windows driver.  This is the worst mode, and should never be used.
const int c_ConnectionModeWindowsDriver   = 2;
/*!
@}
*/



/*!
\defgroup binningstyles Binning Styles

These are the allowed values for StructBinningSettings.BinningStyle
@{
*/
/// No Binning

/// This will disable \ref binning
const int c_BinningStyleNoBinning  = 0;
/// 2x2 Binning

/// This will set the camera to use 2x2 \ref binning
const int c_BinningStyle2x2Binning = 1;
/*!
@}
*/



/*!
\defgroup pixelsummingstyles Pixel Summing Styles

These are the allowed values for StructBinningSettings.PixelSumming
@{
*/
/// Enable Pixel Summing

/// If Enable Pixel Summing is selected, then the binned image will have twice the brightness level, compared to an unbinned image.   This options will not be available if c_BinningStyleNoBinning is selected.
const int c_EnablePixelSumming = 1;
/// Disable Pixel Summing

/// If Disable Pixel Summing is selected, then the binned image will have the same brightness level, compared to an unbinned image.   This options will not be available if c_BinningStyleNoBinning is selected.
const int c_DisablePixelSumming = 2;
/*!
@}
*/



/*!
\defgroup rs422bytevalues RS422 Byte Values

These are the allowed values for MS_SetRS422DataBytes()
@{
*/
/// 7 Data Bytes

/// This will set the RS422 data length to 7 bytes per frame
const int c_RS422_7DataBytes =  7;
/// 8 Data Bytes

/// This will set the RS422 data length to 8 bytes per frame
const int c_RS422_8DataBytes =  8;
/// 9 Data Bytes

/// This will set the RS422 data length to 9 bytes per frame
const int c_RS422_9DataBytes =  9;
/// 10 Data Bytes

/// This will set the RS422 data length to 10 bytes per frame
const int c_RS422_10DataBytes =  10;
/*!
@}
*/



/*!
\defgroup packettypes Packet Types

These are the allowed values for MS_SetPacketType()
@{
*/
/// Normal Packets

/// This indicates that the camera will send the data to the PC using normal-sized packets.  This mode will work on any network, but may result in frames being dropped when downloading from the MS80K cameras.
const int c_PacketTypeNormal = 0;
/// Jumbo Packets

/// This indicates that the camera will send the data to the PC using jumbo-sized packets.  This mode will not work if the network does not support jumbo packets, and is only necessary for the MS80K camera.
const int c_PacketTypeJumbo  = 1;
/*!
@}
*/



/*!
\defgroup timestampdisplaymodes Timestamp Display Modes

These are the allowed values for MS_AVI_SetTimestampDisplayMode()
@{
*/
/// Normal

/// This will save to a series of BMP files.
const int c_TimestampModeNormal = 0;
/// No Day And Month

/// This will save to a series of JPG files.
const int c_TimestampModeNoDayAndMonth = 1;
/// Forced Day And Month

/// This will save to a series of TIF files.
const int c_TimestampModeForcedDayAndMonth = 2;
/*!
@}
*/



/*!
\defgroup boostvalues Boost Values

These are the allowed values for MS_SetBoostValue() for MS70K and MS75K cameras
@{
*/
/// Invalid Boost

/// This indicates that the boost level is invalid
const int c_BoostLevelInvalid = -1;
/// Normal Boost

/// This will set the camera's boost level to Normal
const int c_BoostLevelNormal  =  0;
/// Medium Boost

/// This will set the camera's boost level to Medium
const int c_BoostLevelMedium  =  1;
/// High Boost

/// This will set the camera's boost level to High
const int c_BoostLevelHigh    =  2;
/*!
@}
*/



/*!
\defgroup statuscodes Status Codes

These are the status codes that can be returned by each of the functions in this DLL\n

This list may be expanded in future versions of the DLL

@{
*/
/// OK

/// Everything is ok
const int c_status_OK                                  =   0;
/// Invalid Camera ID

/// The camera ID was invalid.
const int c_status_InvalidCameraID                     = - 1;
/// Timeout Waiting For Mutex

/// This should never happen.  Please contact us if you ever get this error.  It means that one of the threads is blocking another thread.
const int c_status_TimeoutWaitingForMutex              = - 2;
/// Invalid Camera Model

/// The camera model was invalid.
const int c_status_InvalidCameraModel                  = - 3;
/// Invalid Capture Speed

/// The capture speed was invalid.
const int c_status_InvalidCaptureSpeed                 = - 4;
/// Invalid Exposure Time

/// The exposure time was invalid.
const int c_status_InvalidExposureTime                 = - 5;
/// Invalid Gain

/// The gain value was invalid.
const int c_status_InvalidGain                         = - 6;
/// Invalid Trigger Sensitivity

/// The trigger sensitivity value was invalid.
const int c_status_InvalidTriggerSensitivity           = - 9;
/// Camera Is Not Ready To Start Preview

/// You attempted to enter download preview mode when the camera was not ready to do so.
const int c_status_CameraIsNotReadyToStartPreview      = -10;
/// Invalid Preview Position

/// The download preview position was invalid.
const int c_status_InvalidPreviewPos                   = -11;
/// Invalid Download Speed

/// The download speed was invalid.
const int c_status_InvalidDownloadSpeed                = -12;
/// Invalid Download Start Position

/// The download start position was invalid.
const int c_status_InvalidDownloadStartPos             = -13;
/// Invalid Download End Position

/// The download end position was invalid.
const int c_status_InvalidDownloadEndPos               = -14;
/// Invalid Display Mode

/// The display mode was invalid.
const int c_status_InvalidDisplayMode                  = -15;
/// Invalid Vertical Reticle Color

/// The choice for the top left overlay position was invalid.
const int c_status_InvalidChoiceTL                     = -26;
/// Invalid Choice Top Right

/// The choice for the top right overlay position was invalid.
const int c_status_InvalidChoiceTR                     = -27;
/// Invalid Choice Bottom Left

/// The choice for the bottom left overlay position was invalid.
const int c_status_InvalidChoiceBL                     = -28;
/// Invalid Choice Bottom Right

/// The choice for the bottom right overlay position was invalid.
const int c_status_InvalidChoiceBR                     = -29;
/// Invalid AVI File Quality

/// The AVI file quality was invalid.
const int c_status_InvalidAVIFileQuality               = -30;
/// Invalid Save To AVI First Frame

/// The start frame for saving to AVI was invalid.
const int c_status_InvalidSaveToAVIFirstFrame          = -31;
/// Invalid Save To AVI Last Frame

/// The end frame for saving to AVI was invalid.
const int c_status_InvalidSaveToAVILastFrame           = -32;
/// Invalid JPG File Quality

/// The JPEG file quality was invalid.
const int c_status_InvalidJPGFileQuality               = -33;
/// Invalid Save To BMP First Frame

/// The start frame for saving to an image file was invalid.
const int c_status_InvalidSaveToBMPFirstFrame          = -34;
/// Invalid Save To BMP Last Frame

/// The end frame for saving to an image file was invalid.
const int c_status_InvalidSaveToBMPLastFrame           = -35;
/// Invalid Save To BMP Image Type

/// The image type for saving to an image file was invalid.
const int c_status_InvalidSaveToBMPImageType           = -36;
/// Invalid Auto Download Speed

/// The auto-download speed was invalid.
const int c_status_InvalidAutoDownloadSpeed            = -37;
/// Invalid Auto Download Start Frame

/// The auto-download start frame was invalid.
const int c_status_InvalidAutoDownloadStartFrame       = -38;
/// Invalid Auto Download End Frame

/// The auto-download end frame was invalid.
const int c_status_InvalidAutoDownloadEndFrame         = -39;
/// Invalid Auto Download File Type

/// The auto-download file type was invalid.
const int c_status_InvalidAutoDownloadFileType         = -40;
/// Invalid Multi Speed Settings

/// The multi-speed settings were invalid. There are too many possible mistakes to have a separate error code for each of them
const int c_status_InvalidMultiSpeedSettings           = -41;
/// Invalid Image Width

/// The image width was invalid.
const int c_status_InvalidImageWidth                   = -42;
/// Invalid Image Height

/// The image height was invalid.
const int c_status_InvalidImageHeight                  = -43;
/// Invalid Camera Mode

/// The camera mode was invalid.
const int c_status_InvalidCameraMode                   = -44;
/// Invalid Boost

/// The boost value was invalid.
const int c_status_InvalidBoost                        = -45;
/// Invalid Black Offset

/// The black offset value was invalid.
const int c_status_InvalidBlackOffset                  = -46;
/// Invalid Packet Type

/// The requested packet size was invalid.
const int c_status_InvalidPacketType                   = -48;
/// Cannot Recalibrate Now

/// The camera cannot recalibrate now.
const int c_status_CannotRecalibrateNow                = -49;
/// Already Recalibrating

/// The camera is already recalibrating.
const int c_status_AlreadyRecalibrating                = -50;
/// Camera Is Not Capturing

/// The capture cannot be stopped because the camera is currently not capturing.
const int c_status_CameraIsNotCapturing                = -51;
/// Camera ID Already Exists

/// The camera ID that you have requested is already in use.
const int c_status_CameraIDAlreadyExists               = -52;
/// Save In Progress

/// The requested operation cannot be performed because a file save operaton is in progress.
const int c_status_SaveInProgress                      = -53;
/// Lost Camera Connection

/// The connection to the camera has been lost.
const int c_status_LostCameraConnection                = -54;
/// Command Delayed Until Preview Is Updated

/// The requested command was delayed until after the preview image is updated.
const int c_status_CommandDelayedUntilPreviewIsUpdated = -55;
/// DLL Already Initialized

/// Initializing the DLL failed because the DLL is already initialized.
const int c_status_DLLAlreadyInitialized               = -56;
/// DLL Already Closed

/// Closing the DLL failed because the DLL is already closed.
const int c_status_DLLAlreadyClosed                    = -57;
/// File Already Exists

/// The DLL is attempting to overwrite a file that cannot be deleted
const int c_status_FileAlreadyExists                   = -58;
/// File Name Too Long

/// Some functions in the DLL require the file name parameter to be less than 255 characters, and will return this error if the file name is too long
const int c_status_FileNameTooLong                     = -59;
/// Failed To Save Image File

/// The DLL function failed to save the image data to the file
const int c_status_FailedToSaveImageFile               = -60;
/// Failed To Open Setting File

/// The DLL function failed to open a settings file
const int c_status_FailedToOpenSettingFile             = -61;
/// Gigabit Settings Error

/// The DLL function failed to configure the gigabit settings
const int c_status_GigabitSettingsError                = -62;
/// Invalid Download File Type

/// The download destination file type was invalid.
const int c_status_InvalidDownloadFileType             = -63;
/// Invalid Timeout

/// The timeout value was invalid.
const int c_status_InvalidTimeout                      = -64;
/// Invalid Frame Number

/// The frame number was invalid.
const int c_status_InvalidFrameNum                     = -65;
/// Null Pointer

/// The pointer was NULL.
const int c_status_NullPointer                         = -66;
/// Invalid Trigger Type

/// The trigger type is invalid
const int c_status_InvalidTriggerType                  = -67;
/// Capture In Progress

/// The setting cannot be changed because a capture is in progress
const int c_status_CaptureInProgress                   = -68;
/// Invalid Error Code

/// The error code is invalid
const int c_status_InvalidErrorCode                    = -69;
/// Invalid Binning Style

/// The \ref binning style is invalid
const int c_status_InvalidBinningStyle                 = -70;
/// Invalid Pixel Summing

/// The pixel summing value is invalid
const int c_status_InvalidPixelSumming                 = -71;
/// Invalid ROI X Offset

/// The ROI X offset is invalid
const int c_status_InvalidROIXOffset                   = -73;
/// Invalid ROI Y Offset

/// The ROI Y offset is invalid
const int c_status_InvalidROIYOffset                   = -74;
/// Changing Camera Mode

/// The DLL is currently in the process of changing the camera mode.
const int c_status_ChangingCameraMode                  = -75;
/// Already In Download Mode

/// The DLL is already in download mode.
const int c_status_AlreadyInDownloadMode               = -76;
/// Camera Is Not Idle

/// The requested operation can only be performed when the camera is idle.
const int c_status_CameraIsNotIdle                     = -77;
/// Error Opening AVI File

/// Something went wrong when trying to open an AVI file
const int c_status_ErrorOpeningAVIFile                 = -79;
/// Invalid MAC Address

/// An invalid MAC address was passed to the MS_GenerateCameraIDFromMACAddress() function
const int c_status_InvalidMACAddress                   = -80;
/// Error Checking Camera Type

/// Something went wrong when checking the camera type.  This camera is not recognized by this version of the DLL.
const int c_status_ErrorCheckingCameraType             = -82;
/// Error Initializing AVI File

/// Something went wrong when initializing the AVI file.  One of the Mega Speed DLLs might not be properly installed
const int c_status_ErrorInitializingAVIFile            = -83;
/// Error Writing To AVI File

/// Something went wrong when writing to the AVI file.  The AVI file may be open in another program.
const int c_status_ErrorWritingToAVIFile               = -84;
/// Error Initializing Codec

/// Something went wrong when compressing the AVI file.  The \ref indeo video compressor might not be properly installed.
const int c_status_ErrorInitializingCodec              = -85;
/// Error Compressing AVI File

/// Something went wrong when compressing the AVI file.  The \ref indeo video compressor might not be compatible with the current image height.
const int c_status_ErrorCompressingAVIFile             = -86;
/// Invalid RS422 Data Bytes

/// The selected number of RS422 data bytes was invalid.
const int c_status_InvalidRS422DataBytes               = -87;
/// Callback In Progress

/// The requested operation cannot be performed because the DLL is waiting for a callback function to complete.
const int c_status_CallbackInProgress                  = -88;
/// Changing Image Size

/// The requested operation cannot be performed because the DLL is currently changing the image size.
const int c_status_ChangingImageSize                   = -89;
/// Feature Not Available In This Mode

/// The requested feature is not available in this capture mode.
const int c_status_FeatureNotAvailableInThisMode       = -93;
/// Invalid Parameter

/// The parameter was invalid.
const int c_status_InvalidParameter                    = -94;
/// Feature Not Available

/// You tried to use a feature that is not available for this camera model.
const int c_status_FeatureNotAvailable                 = -95;
/// Timeout Waiting For Thread To Exit

/// This should never happen.  Please contact us if you ever get this error.  It means one of the threads is not exiting.
const int c_status_TimeoutWaitingForThreadToExit       = -96;
/// Timeout Waiting For Image Buffers

/// This should never happen.  Please contact us if you ever get this error.  It means that the image buffers are not responding.
const int c_status_TimeoutWaitingForImageBuffers       = -97;
/// Direct Show Error

/// One of the DirectShow functions failed to complete successfully - possibly because DirectShow is not installed properly.
const int c_status_DirectShowError                     = -98;
/// Out Of Memory

/// The DLL failed to allocate memory, because there is no free memory remaining.
const int c_status_OutOfMemory                         = -99;
/// Other Error

/// An error occurred that is not in this list.  This should never happen.  Please contact us if you ever get this error.
const int c_status_OtherError                          =-100;

/// Invalid Auto-Exposure Target Value

/// The Auto-Exposure Target Value was invalid.
const int c_status_InvalidAutoExposureTargetValue     = -120;
/// Invalid Auto-Exposure Error Margin

/// The Auto-Exposure Error Margin was invalid.
const int c_status_InvalidAutoExposureErrorMargin     = -121;
/// Invalid Auto-Exposure Max Exposure Time

/// The Auto-Exposure Max Exposure Time was invalid.
const int c_status_InvalidAutoExposureMaxExposureTime = -123;
/// Invalid Auto-Exposure Window Width

/// The Auto-Exposure Window Width was invalid.
const int c_status_InvalidAutoExposureWindowWidth     = -124;
/// Invalid Auto-Exposure Window Height

/// The Auto-Exposure Window Height was invalid.
const int c_status_InvalidAutoExposureWindowHeight    = -125;
/// Invalid Auto-Exposure Target Location X

/// The Auto-Exposure Target Location X was invalid.
const int c_status_InvalidAutoExposureTargetLocationX = -126;
/// Invalid Auto-Exposure Target Location Y

/// The Auto-Exposure Target Location Y was invalid.
const int c_status_InvalidAutoExposureTargetLocationY = -127;
/// Invalid Auto-Exposure Min Exposure Time

/// The Auto-Exposure Min Exposure Time was invalid.
const int c_status_InvalidAutoExposureMinExposureTime = -130;

/*!
@}
*/

/*!
@}
*/

/***************************************************************************************************************************************/

/*! \defgroup cameracontrolfunctions Camera Control Functions

These are the functions that are used to control the camera, and the DLL.

These functions are divided into the following categories:\n
\n
\ref initializationfunctions
\n
\copydoc initializationfunctions
\n
\n
\ref utilityfunctions
\n
\copydoc utilityfunctions
\n
\n
\ref writesettingstructfunctions
\n
\copydoc writesettingstructfunctions
\n
\n
\ref readsettingstructfunctions
\n
\copydoc readsettingstructfunctions
\n
\n
\ref readstatusstructfunctions
\n
\copydoc readstatusstructfunctions
\n
\n
\ref individualsettingsfunctions
\n
\copydoc individualsettingsfunctions
\n
\n
\ref individualstatusfunctions
\n
\copydoc individualstatusfunctions
\n
\n
\ref cameramodelspecificfunctions
\n
\copydoc cameramodelspecificfunctions
\n
\n
\ref cameratypecheckingfunctions
\n
\copydoc cameratypecheckingfunctions
\n
\n
\ref cameraboundscheckingfunctions
\n
\copydoc cameraboundscheckingfunctions
\n
\n
\ref cameramodechangingfunctions
\n
\copydoc cameramodechangingfunctions
\n
\n
\ref filewritingfunctions
\n
\copydoc filewritingfunctions
\n
\n
\ref imagebufferfunctions
\n
\copydoc imagebufferfunctions
\n
\n

@{
*/

/*! \defgroup initializationfunctions Initialization Functions

These functions are used for initializing and closing the DLL, setting up or cleaning up a Camera ID, and connecting to or disconnecting from the camera.

@{
*/

/// Initialize the DLL

///	You must call this function to initialize the DLL, before you can use any of the other functions in the DLL.\n
/// One exception to this is the MS_StartLoggingToFile() function, which is safe to call even if the DLL has not been initialized yet.\n
/// Calling this function a second time, when the DLL has already been initialized, will have no effect.\n
/// \attention If you attempt to call any of the other functions in this DLL before calling this function, the DLL will crash!!!\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_InitializeDLL(int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Close the DLL

///	You must call this function when your application is finished using the DLL, to free the memory that was reserved by the DLL.\n
///  Calling this function a second time, when the DLL has already been closed, will have no effect.\n
/// \attention Do not attempt to call MS_InitializeDLL() after you have called MS_CloseDLL().  The DLL may fail to reinitialize.\n
///  MS_InitializeDLL() must only be called once, when you are ready to initialize the DLL,
///   and MS_CloseDLL() must only be called once, when you are ready to close the DLL.
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_CloseDLL(int* pStatus = NULL ///< \copydoc pstatus
									 );


/// Initialize Camera ID

/// Before you can connect to a camera, you must call this function to initialize a camera ID to use to identify the camera.\n
/// This function will allocate the memory required for the camera's image buffers, and will prepare the DLL to accept commands for this camera.\n
/// Each MAC address will be assigned a unique CameraID value.\n
/// \attention Make sure you save the returned CameraID value.\n
///  This is the value that you must pass as the CameraID parameter to all the other functions in this DLL.
/// \return the new camera ID if successful\n
///   the value of *pStatus if unsuccessful\n
MS_CAMERACONTROL_API long MS_InitializeCameraID(
///     The MAC Address of the camera you want to connect to\n
												const char* MACAddress,
												int* pStatus = NULL ///< \copydoc pstatus
												);

/// Clean Up Camera ID

/// Use this function to free the camera ID, and free the PC RAM that was reserved by the camera.\n
/// This function is called automatically for each camera when you call MS_CloseDLL().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_CleanupCameraID(long CameraID, ///< \copydoc cameraid
											int* pStatus = NULL ///< \copydoc pstatus
											);

/// Cleanup Camera ID With Callback Step 1

/// If you get a ::c_status_TimeoutWaitingForThreadToExit error message when you use the MS_CleanupCameraID() function, then you will need to use this function instead.\n
/// This function will call \ref MS_SetCallback_CleanupCameraID() "Callback_CleanupCameraID()".\n
/// In your \ref MS_SetCallback_CleanupCameraID() "Callback_CleanupCameraID()" handler function, you will need to call the MS_CleanupCameraIDWithCallbackStep2() function.\n
/// Make sure that MS_CleanupCameraIDWithCallbackStep2() is called from the same thread that was used to call MS_InitializeCameraID().\n
/// You may need to use the PostMessage() function in the callback function in order to accomplish this.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_CleanupCameraIDWithCallbackStep1(long CameraID, ///< \copydoc cameraid
															 int* pStatus = NULL ///< \copydoc pstatus
															 );

/// Cleanup Camera ID With Callback Step 2

/// This function must only be called from your \ref MS_SetCallback_CleanupCameraID() "Callback_CleanupCameraID()" handler function.  See MS_CleanupCameraIDWithCallbackStep1().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_CleanupCameraIDWithCallbackStep2(long CameraID, ///< \copydoc cameraid
															 int* pStatus = NULL ///< \copydoc pstatus
															 );




/// Check If Camera ID Is Valid

/// Use this function to check if the specified camera ID is valid.\n
/// The camera ID will be valid if the call to MS_InitializeCameraID() has succeeded for this camera, and you have not called MS_CleanupCameraID() on this ID since then.\n
/// The camera ID will be invalid any other time.\n
/// \return <b>true</b> if the camera ID is valid\n
///   <b>false</b> if the camera ID is invalid\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraIDIsValid(long CameraID, ///< \copydoc cameraid
													int* pStatus = NULL ///< \copydoc pstatus
													);



/// Find Available Camera MAC Address

/// This function will detect which cameras are available on the network.\n
/// If only one camera is available, this function will automatically return its MAC address\n
/// If no cameras are available, then this function will return an empty string.\n
/// If there is more than one camera available, then this function will return an empty string,
///   and you should use the MS_ShowCameraSelectDialogAndReturnMACAddress() function to select a camera and find its MAC address.\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_FindAvailableCameraMACAddress(
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
///     a pointer to a variable to update with the number of available cameras found.  If this is NULL, then the value will not be updated.\n
///     \attention pNumCamerasFound will always be either 0, 1, or 2.  If more than 2 cameras are found, pNumCamerasFound will still be set to 2.\n
															int* pNumCamerasFound = NULL,
///     The number of milliseconds to scan for cameras on the network.  The default value of 100 should be sufficient for any situation.\n
															int timeout = 100,
															int* pStatus = NULL ///< \copydoc pstatus
															);


/// Show Camera Select Dialog And Return MAC Address

/// This function will show the Camera Select dialog, which you can use to see which cameras are available, and select a camera to connect to.\n
///  If the user successfully selects a camera, then this function will return its MAC address.\n
///  If the user does not successfully select a camera, then this function will return an empty string.\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_ShowCameraSelectDialogAndReturnMACAddress(
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
															int* pStatus = NULL ///< \copydoc pstatus
															);

/// Connect To Camera

/// This function will attempt to connect to the camera with the MAC address for this CameraID.\n
/// If the function succeeded in connecting to the camera, then it will return <b>true</b>.\n
/// If the function failed to connect to the camera, then it will return <b>false</b>.\n
/// \return the result of the connection attempt, as described above\n
MS_CAMERACONTROL_API bool MS_ConnectToCamera(long CameraID, ///< \copydoc cameraid
///     The number of milliseconds to scan for cameras on the network.  The default value of 100 should be sufficient for any situation.\n
											 int timeout = 100,
											 int* pStatus = NULL ///< \copydoc pstatus
											 );

/*!
@}
*/

/*! \defgroup utilityfunctions Utility Functions

These functions perform various useful tasks that didn't belong in any other category.

@{
*/

/// Check Camera Connection

/// This function will send a poll command to the camera to detect if it is still connected.\n
/// This function will return <b>true</b> if the camera is still connected, or <b>false</b> if the camera is not connected.\n
/// \attention Calling this function while a download is in progress will cause frames to be dropped!\n
/// \return the camera's connection status, as described above\n
MS_CAMERACONTROL_API bool MS_CheckCameraConnection(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );



/// Read AVI File Data

/// This function reads the embedded data from an AVI file\n
/// \return a StructDataFromAVIFile structure containing the data from the AVI file\n
///   if something goes wrong when reading the file, then StructDataFromAVIFile.totalFrames will be -1\n
StructDataFromAVIFile MS_ReadAVIFileData(long CameraID, ///< \copydoc cameraid
												const char* FileName,  ///< The filename of the AVI file to read
												int* pStatus = NULL ///< \copydoc pstatus
											);



/// Extract RS422 Data To File

/// This function reads the embedded RS422 data from an AVI file, and extracts it to a text file.\n
/// Each line in the text file will contain the RS422 data from one frame in the AVI file, as a string of hexadecimal characters, in the same format as the MS_ReadRS422DataFromFrame() function.
/// The length of the string will be determined by the number of RS422 data bytes, as specified by the MS_SetRS422DataBytes() function.\n
/// Each byte of data will be 2 hexadecimal characters.\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ExtractRS422DataToFile(long CameraID, ///< \copydoc cameraid
												   const char* AVIFileName,  ///< The filename of the AVI file to read
												   const char* DataFileName,  ///< The filename of the data file to write
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Count DLL Instances

/// This function will count how many instances of the DLL are currently open.\n
/// \return the number of instances found, including the current instance\n
MS_CAMERACONTROL_API int MS_CountDLLInstances(int* pStatus = NULL ///< \copydoc pstatus
											  );


/// Get Capture Mode String

/// This function will convert the camera mode and trigger type numbers to a string describing the capture mode\n
/// updates pString with the capture mode string\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_GetCaptureModeString(
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
///     The camera mode value, as reported by StructCameraStatus::CameraMode\n
														 int CameraMode,
///     The trigger type value, as reported by StructCameraStatus::TriggerType\n
														 int TriggerType,
														 int* pStatus = NULL ///< \copydoc pstatus
														 );

/// Get Error Message Short

/// This function will convert an error code number to the short version of the error message string\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_GetErrorMessageShort(
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
///     This is the error code that you want to convert to an error message string.\n
														 int errorCode,
														 int* pStatus = NULL ///< \copydoc pstatus
														 );


/// Get Error Message Long

/// This function will convert an error code number to the long version of the error message string\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_GetErrorMessageLong(
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
///     This is the error code that you want to convert to an error message string.\n
														int errorCode,
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Ignore Lost Connection Errors Until Camera Is Connected

/// This function will tell the DLL whether or not to ignore ::c_status_LostCameraConnection error messages until after the first time the camera is successfully connected\n
/// This will prevent the DLL from reporting error messages if you try to set the camera's settings before you connect to the camera.\n
/// By default, the ::c_status_LostCameraConnection error message is always enabled\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_IgnoreLostConnectionErrorsUntilCameraIsConnected(long CameraID, ///< \copydoc cameraid
///     if this is <b>true</b>, then ::c_status_LostCameraConnection error messages will be ignored until after the first time the camera is successfully connected\n
///     if this is <b>false</b>, then ::c_status_LostCameraConnection error messages will always be reported, even if you haven't connected to the camera yet\n
																			 bool ignore,
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Get Last Error

/// This function will report the last error code that the DLL recorded.\n
/// \return the last error that the DLL recorded, or ::c_status_OK if no errors have been recorded yet\n
MS_CAMERACONTROL_API int MS_GetLastError();

/// Reset Error Code

/// This function will reset the DLL's last error code to ::c_status_OK, so that you can use the MS_GetLastError() function to check if the same error is occurring more than once\n
/// \return the last error that the DLL recorded, or ::c_status_OK if no errors have been recorded yet\n
MS_CAMERACONTROL_API int MS_ResetErrorCode();

/// Get Packet Type

/// Use this function to get the current packet type\n
/// For a list of allowed values, see \ref packettypes\n
/// \return the current packet type\n
MS_CAMERACONTROL_API int MS_GetPacketType(long CameraID, ///< \copydoc cameraid
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Set Packet Type

/// Use this function to get the current packet type\n
/// For a list of allowed values, see \ref packettypes\n
/// This change will not be applied until you disconnect from the camera and reconnect.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetPacketType(long CameraID, ///< \copydoc cameraid
///     the packet type\n
										  int newPacketType,
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Get Last Capture Camera Mode

/// Use this function to get the capture mode of the camera's most recent capture\n
/// This is the value that StructCameraStatus::CameraMode was set to during the most recent capture.\n
/// For a list of allowed values, see \ref cameramodevalues\n
/// \return the capture mode of the camera's most recent capture\n
MS_CAMERACONTROL_API int MS_GetLastCaptureCameraMode(long CameraID, ///< \copydoc cameraid
													 int* pStatus = NULL ///< \copydoc pstatus
													 );

/// Get Last Capture Trigger Type

/// Use this function to get the trigger type of the camera's most recent capture\n
/// This is the value that StructCameraStatus::TriggerType was set to during the most recent capture.\n
/// For a list of allowed values, see \ref triggertypevalues\n
/// \return the trigger type of the camera's most recent capture\n
MS_CAMERACONTROL_API int MS_GetLastCaptureTriggerType(long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );


/// Save Settings To Preset File

/// Use this function to save the camera's preset settings to a preset file.\n
/// The following values are saved to the camera preset file:\n
/// StructCameraStatus::CameraMode\n
/// StructCameraStatus::TriggerType\n
/// StructCurrentImageSize::ImageWidthInCameraBeforeBinning\n
/// StructCurrentImageSize::ImageHeightInCameraBeforeBinning\n
/// StructBasicCaptureSettings::CaptureSpeed\n
/// StructBasicCaptureSettings::ExposureTime\n
/// StructBasicCaptureSettings::GainValue\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SaveSettingsToPresetFile(long CameraID, ///< \copydoc cameraid
///     This is the filename of the preset file that you want to save the camera's current settings to.\n
													 const char* FileName,
													 int* pStatus = NULL ///< \copydoc pstatus
													 );


/// Load Settings From Preset File

/// Use this function to load the camera's preset settings from a preset file.\n
/// See also MS_SaveSettingsToPresetFile()
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_LoadSettingsFromPresetFile(long CameraID, ///< \copydoc cameraid
///     This is the filename of the preset file that you want to load the camera's current settings from.\n
													   const char* FileName,
													   int* pStatus = NULL ///< \copydoc pstatus
													   );




/*!
@}
*/

/*! \defgroup writesettingstructfunctions Camera Write Settings Struct Functions

These functions are used to update the camera's settings structs.  See \ref camerasettingstructs

@{
*/

/// Set Basic Capture Settings

/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetBasicCaptureSettings    (long CameraID, ///< \copydoc cameraid
														StructBasicCaptureSettings    BasicCaptureSettings    , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Advanced Capture Settings

/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetAdvancedCaptureSettings (long CameraID, ///< \copydoc cameraid
														StructAdvancedCaptureSettings AdvancedCaptureSettings , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Download Settings

/// \return the value of *pStatus\n
int MS_SetDownloadSettings								(long CameraID, ///< \copydoc cameraid
														const StructDownloadSettings &DownloadSettings        , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Color Settings

/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetColorSettings           (long CameraID, ///< \copydoc cameraid
														StructColorSettings           ColorSettings           , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);


/// Set Overlay Settings

/// \return the value of *pStatus\n
int MS_SetOverlaySettings								(long CameraID, ///< \copydoc cameraid
														const StructOverlaySettings &OverlaySettings         , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set AVI File Settings

/// \return the value of *pStatus\n
int MS_SetAVIFileSettings								(long CameraID, ///< \copydoc cameraid
														const StructAVIFileSettings &AVIFileSettings         , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Image File Settings

/// \return the value of *pStatus\n
int MS_SetImageFileSettings								(long CameraID, ///< \copydoc cameraid
														const StructImageFileSettings &ImageFileSettings       , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Auto Download Settings

/// \return the value of *pStatus\n
int MS_SetAutoDownloadSettings							(long CameraID, ///< \copydoc cameraid
														const StructAutoDownloadSettings &AutoDownloadSettings    , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Multi Speed Settings

/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetMultiSpeedSettings      (long CameraID, ///< \copydoc cameraid
														StructMultiSpeedSettings      MultiSpeedSettings      , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Binning Settings

/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetBinningSettings         (long CameraID, ///< \copydoc cameraid
														StructBinningSettings         BinningSettings         , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/// Set Auto-Exposure Settings

/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetAutoExposureSettings     (long CameraID, ///< \copydoc cameraid
														StructAutoExposureSettings         AutoExposureSettings         , ///< This struct must contain the new values that you want to update this settings struct with.
														bool resetInvalidParametersToDefaults = true, ///< \copydoc resetinvalidparameterstodefaults
														int* pStatus = NULL ///< \copydoc pstatus
														);

/*!
@}
*/

/*! \defgroup readsettingstructfunctions Camera Read Settings Struct Functions

These functions are used to read the current values of the camera's settings structs.  See \ref camerasettingstructs

@{
*/

/// Get Basic Capture Settings

/// \return a struct containing the current values of the settings\n
MS_CAMERACONTROL_API const StructBasicCaptureSettings     MS_GetBasicCaptureSettings   (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Advanced Capture Settings

/// \return a struct containing the current values of the settings\n
MS_CAMERACONTROL_API const StructAdvancedCaptureSettings  MS_GetAdvancedCaptureSettings(long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Download Settings

/// \return a struct containing the current values of the settings\n
const StructDownloadSettings         MS_GetDownloadSettings       (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Color Settings

/// \return a struct containing the current values of the settings\n
MS_CAMERACONTROL_API const StructColorSettings            MS_GetColorSettings          (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);


/// Get Overlay Settings

/// \return a struct containing the current values of the settings\n
const StructOverlaySettings          MS_GetOverlaySettings        (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get AVI File Settings

/// \return a struct containing the current values of the settings\n
const StructAVIFileSettings          MS_GetAVIFileSettings        (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Image File Settings

/// \return a struct containing the current values of the settings\n
const StructImageFileSettings        MS_GetImageFileSettings      (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Auto Download Settings

/// \return a struct containing the current values of the settings\n
const StructAutoDownloadSettings     MS_GetAutoDownloadSettings   (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Multi Speed Settings

/// \return a struct containing the current values of the settings\n
MS_CAMERACONTROL_API const StructMultiSpeedSettings       MS_GetMultiSpeedSettings     (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Binning Settings

/// \return a struct containing the current values of the settings\n
MS_CAMERACONTROL_API const StructBinningSettings          MS_GetBinningSettings        (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Auto-Exposure Settings

/// \return a struct containing the current values of the settings\n
MS_CAMERACONTROL_API const StructAutoExposureSettings          MS_GetAutoExposureSettings        (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/*!
@}
*/

/*! \defgroup readstatusstructfunctions Camera Read Status Struct Functions

These functions are used to read the current values of the camera's status structs.  See \ref camerastatusstructs

@{
*/

/// Get Camera Status

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructCameraStatus             MS_GetCameraStatus           (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Capture Status

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructCaptureStatus            MS_GetCaptureStatus          (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Current Image Size

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructCurrentImageSize         MS_GetCurrentImageSize       (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Camera Temperature

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructCameraTemperature        MS_GetCameraTemperature      (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Preview Status

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructPreviewStatus            MS_GetPreviewStatus          (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Download Status

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructDownloadStatus           MS_GetDownloadStatus         (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get File Status

/// \return a struct containing the current values of the status\n
const StructFileStatus               MS_GetFileStatus             (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Buffer Status

/// \return a struct containing the current values of the status\n
MS_CAMERACONTROL_API const StructBufferStatus             MS_GetBufferStatus           (long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);

/// Get Gigabit Connection Status

/// \return a struct containing the current values of the status\n
const StructGigabitConnectionStatus  MS_GetGigabitConnectionStatus(long CameraID, ///< \copydoc cameraid
																						int* pStatus = NULL ///< \copydoc pstatus
																						);


/*!
@}
*/
/*! \defgroup individualsettingsfunctions Individual Camera Settings Functions
These functions are used to get individual status values for the camera, which aren't contained in any of the \ref cameracontrolstructs .
@{
*/

/// Set Post-Trigger Frames

/// Use this function to set the number of frames to capture after the trigger pulse in Pre/Post Trigger mode.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetPostTriggerFrames(long CameraID, ///< \copydoc cameraid
								/// The number of frames to capture after the trigger.\n
												long PostTriggerFrames, /// 
												int* pStatus = NULL ///< \copydoc pstatus
												);

/// Get Post-Trigger Frames

/// Use this function to get the number of frames to capture after the trigger pulse in Pre/Post Trigger mode.\n
/// \return the number of frames to capture after the trigger pulse\n
MS_CAMERACONTROL_API int MS_GetPostTriggerFrames(long CameraID, ///< \copydoc cameraid
												int* pStatus = NULL ///< \copydoc pstatus
												);

/// Get Post-Trigger Start Pos

/// Use this function to get the frame number the trigger pulse occured in Pre/Post Trigger mode.\n
/// \return the frame number where the trigger pulse occured.\n
MS_CAMERACONTROL_API int MS_GetPostTriggerStartPos(long CameraID, ///< \copydoc cameraid
													int* pStatus = NULL ///< \copydoc pstatus
													);

/// Get Post-Trigger Looped Through

/// Use this function to determine if the post trigger frames looped past end of camera RAM.\n
/// \return the number of milliseconds that have elapsed since the capture was started\n
/// \return <b>true</b> if frames looped back to the begining of camera RAM, or <b>false</b> if they did not.\n
MS_CAMERACONTROL_API bool MS_GetPostTriggerLoopedThrough(long CameraID, ///< \copydoc cameraid
														int* pStatus = NULL ///< \copydoc pstatus
														);

/*!
@}
*/




/*! \defgroup individualstatusfunctions Individual Camera Status Functions
These functions are used to get individual status values for the camera, which aren't contained in any of the \ref cameracontrolstructs .
@{
*/

/// Get Time Elapsed

/// Use this function to get the number of milliseconds that have elapsed since the capture was started.\n
/// \return the number of milliseconds that have elapsed since the capture was started\n
MS_CAMERACONTROL_API double MS_GetTimeElapsed(long CameraID, ///< \copydoc cameraid
											  int* pStatus = NULL ///< \copydoc pstatus
											  );

/// Get Last Capture Start Time

/// Use this function to get the time that the last capture was started at, in SYSTEMTIME format.\n
/// \return the time that the last capture was started at, in SYSTEMTIME format\n
MS_CAMERACONTROL_API SYSTEMTIME MS_GetLastCaptureStartTime(long CameraID, ///< \copydoc cameraid
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Get CPU Usage

/// Use this function to get the current CPU usage, as a value from 0 to 100.\n
/// \return the current CPU usage, as a value from 0 to 100.\n
MS_CAMERACONTROL_API int MS_GetCPUUsage(int* pStatus = NULL ///< \copydoc pstatus
										);

/// Get Max CPU Usage

/// Use this function to get the maximum value that the CPU usage has reached in the past 30 seconds, as a value from 0 to 100.\n
/// \return the maximum value that the CPU usage has reached in the past 30 seconds, as a value from 0 to 100\n
MS_CAMERACONTROL_API int MS_GetMaxCPUUsage(int* pStatus = NULL ///< \copydoc pstatus
										   );


/// Get DLL Version

/// Use this function to get the DLL version number.\n
/// This is the version number of the DLL itself.\n
/// This number will not depend on the camera model that you selected.\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_GetDLLVersion(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
												  int* pStatus = NULL ///< \copydoc pstatus
												  );

/// Get Frontend Version

/// Use this function to get the Frontend version number.\n
/// This is the version number that will be displayed in the frontend, which will approximately match the camera's firmware version.\n
/// This number will be different depending on the camera model that you selected.\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_GetFrontendVersion(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
												  int* pStatus = NULL ///< \copydoc pstatus
												  );

/*!
@}
*/

/*! \defgroup cameramodelspecificfunctions Camera Model-Specific Functions

These functions are used to get or set individual setting values for the camera, which aren't contained in any of the \ref cameracontrolstructs , and are only available in some camera models.

@{
*/

/// Get Black Offset Value

/// Use this function to get the camera's black offset value.\n
/// Use the MS_CheckIfCameraHasBlackOffsetValue() function to check if this camera supports this function.\n
/// \return the camera's black offset value\n
MS_CAMERACONTROL_API int MS_GetBlackOffsetValue(long CameraID, ///< \copydoc cameraid
												int* pStatus = NULL ///< \copydoc pstatus
												);

/// Set Black Offset Value

/// Use this function to set the camera's black offset value.\n
/// Use the MS_CheckIfCameraHasBlackOffsetValue() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetBlackOffsetValue(long CameraID, ///< \copydoc cameraid
///     the camera's black offset value\n
												int blackOffsetValue,
												int* pStatus = NULL ///< \copydoc pstatus
												);

/// Get ROI X Offset Value

/// Use this function to get the camera's Region of Interest X offset value.\n
/// Use the MS_CheckIfCameraHasROIXandYOffsetValue() function to check if this camera supports this function.\n
/// \return the camera's ROI X offset value\n
MS_CAMERACONTROL_API int MS_GetROIXOffsetValue(long CameraID, ///< \copydoc cameraid
											   int* pStatus = NULL ///< \copydoc pstatus
											   );

/// Set ROI X Offset Value

/// Use this function to set the camera's Region of Interest X offset value.\n
/// Use the MS_CheckIfCameraHasROIXandYOffsetValue() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetROIXOffsetValue(long CameraID, ///< \copydoc cameraid
///     the camera's ROI X offset value\n
											   int XOffsetValue,
											   int* pStatus = NULL ///< \copydoc pstatus
											   );

/// Get ROI Y Offset Value

/// Use this function to get the camera's Region of Interest Y offset value.\n
/// Use the MS_CheckIfCameraHasROIXandYOffsetValue() function to check if this camera supports this function.\n
/// \return the camera's ROI Y offset value\n
MS_CAMERACONTROL_API int MS_GetROIYOffsetValue(long CameraID, ///< \copydoc cameraid
											   int* pStatus = NULL ///< \copydoc pstatus
											   );

/// Set ROI Y Offset Value

/// Use this function to set the camera's Region of Interest Y offset value.\n
/// Use the MS_CheckIfCameraHasROIXandYOffsetValue() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetROIYOffsetValue(long CameraID, ///< \copydoc cameraid
///     the camera's ROI Y offset value\n
											   int ROIYOffsetValue,
											   int* pStatus = NULL ///< \copydoc pstatus
											   );

/// Get ROI Auto Center Value

/// Use this function to check if auto-centering the image's Region of Interest is enabled.\n
/// Use the MS_CheckIfCameraHasROIXandYOffsetValue() function to check if this camera supports this function.\n
/// \return <b>true</b> if ROI auto-centering is enabled, <b>false</b> if auto-centering is disabled.\n
MS_CAMERACONTROL_API bool MS_GetROIAutoCenterValue(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Set ROI Auto Center Value

/// Use this function to enable or disable auto-centering the image's Region of Interest.\n
/// Use the MS_CheckIfCameraHasROIXandYOffsetValue() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetROIAutoCenterValue(long CameraID, ///< \copydoc cameraid
///     <b>true</b> to enable auto-centering, <b>false</b> to disable auto-centering.\n
											      bool ROIAutoCenterValue,
											      int* pStatus = NULL ///< \copydoc pstatus
											      );

/// Get \ref timeout

/// Use this function to get the number of milliseconds that the camera is allowed to capture for before the capture is automatically stopped, to prevent overheating.\n
/// Use the MS_CheckIfCameraHasTimeout() function to check if this camera supports this function.\n
/// To calculate the number of milliseconds remaining before the current capture will time out, subtract the value returned by MS_GetTimeElapsed() from this value\n
/// \return the \ref timeout value, in milliseconds\n
MS_CAMERACONTROL_API int MS_GetTimeout(long CameraID, ///< \copydoc cameraid
									   int* pStatus = NULL ///< \copydoc pstatus
									   );

/// Set \ref timeout

/// Use this function to set the number of milliseconds that the camera is allowed to capture for before the capture is automatically stopped, to prevent overheating.\n
/// Use the MS_CheckIfCameraHasTimeout() function to check if this camera supports this function.\n
/// To calculate the number of milliseconds remaining before the current capture will time out, subtract the value returned by MS_GetTimeElapsed() from this value\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetTimeout(long CameraID, ///< \copydoc cameraid
///     the \ref timeout value, in milliseconds\n
									   int timeout,
									   int* pStatus = NULL ///< \copydoc pstatus
									   );

/// Check If ESwitch Is Enabled

/// Use this function to check if the ESwitch feature is enabled.\n
/// Use the MS_CheckIfCameraHasESwitch() function to check if this camera supports this function.\n
/// \return true if ESwitch is enabled, false otherwise\n
MS_CAMERACONTROL_API int MS_CheckIfESwitchIsEnabled(long CameraID, ///< \copydoc cameraid
										      int* pStatus = NULL ///< \copydoc pstatus
										      );

/// Get RS422 Bytes

/// Use this function to get the number of bytes of RS422 data that will be stored on each image frame.\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// For a list of allowed values, see \ref rs422bytevalues\n
/// \return the number of RS422 data bytes\n
MS_CAMERACONTROL_API int MS_GetRS422DataBytes(long CameraID, ///< \copydoc cameraid
										      int* pStatus = NULL ///< \copydoc pstatus
										      );

/// Use Marker As Marker

/// Use this function to use the camera's marker input for marker signals.\n
/// Use the MS_CheckIfCameraHasESwitch() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_UseMarkerAsMarker(long CameraID, ///< \copydoc cameraid
									       int* pStatus = NULL ///< \copydoc pstatus
									       );

/// Use Marker As ESwitch

/// Use this function to use the camera's marker input for ESwitch signals.\n
/// Use the MS_CheckIfCameraHasESwitch() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_UseMarkerAsESwitch(long CameraID, ///< \copydoc cameraid
									       int* pStatus = NULL ///< \copydoc pstatus
									       );

/// Set RS422 Bytes

/// Use this function to set the number of bytes of RS422 data that will be stored on each image frame.\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// For a list of allowed values, see \ref rs422bytevalues\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetRS422DataBytes(long CameraID, ///< \copydoc cameraid
///     the number of bytes of RS422 data that will be stored on each image frame\n
									       int RS422DataBytes,
									       int* pStatus = NULL ///< \copydoc pstatus
									       );

/// Get RS422 Is Inverted

/// Use this function to check if the RS422 data is inverted.\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// \return <b>true</b> if RS422 data is inverted, or <b>false</b> if RS422 data is not inverted.\n
MS_CAMERACONTROL_API bool MS_GetRS422IsInverted(long CameraID, ///< \copydoc cameraid
											   int* pStatus = NULL ///< \copydoc pstatus
											   );

/// Set RS422 Is Inverted

/// Use this function to select whether or not the RS422 data is inverted.\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetRS422IsInverted(long CameraID, ///< \copydoc cameraid
///     If this is <b>true</b>, then the RS422 data will be inverted.  If this is <b>false</b> then the RS422 data will not be inverted.\n
									          bool RS422IsInverted,
									          int* pStatus = NULL ///< \copydoc pstatus
									          );

/// Check If RS422 Is Locked

/// Use this function to check if the camera's RS422 input is locked\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// \return <b>true</b> if the camera has locked on to the incoming RS422 data stream\n
///   <b>false</b> if the camera has not locked onto the RS422 data stream yet, and no RS422 data is available to the camera\n
MS_CAMERACONTROL_API bool MS_CheckIfRS422IsLocked(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );


/// Set Preview Throttling Rate

/// Use this function to set the camera's preview throttling rate.  This will be the number of preview frames skipped after every preview frame that is sent from the camera.\n
/// Use the MS_CheckIfCameraHasPreviewThrottling() function to check if this camera supports this function.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetPreviewThrottlingRate(long CameraID, ///< \copydoc cameraid
///     the number of frames to skip.  setting this to 31 disables the preview frames entirely
									          int PreviewThrottlingRate,
									          int* pStatus = NULL ///< \copydoc pstatus
									          );

/// Get Preview Throttling Rate

/// Use this function to get the camera's preview throttling rate.  This will be the number of preview frames skipped after every preview frame that is sent from the camera.\n
/// Use the MS_CheckIfCameraHasPreviewThrottling() function to check if this camera supports this function.\n
/// \return the camera's preview throttling rate\n
MS_CAMERACONTROL_API int MS_GetPreviewThrottlingRate(long CameraID, ///< \copydoc cameraid
									          int* pStatus = NULL ///< \copydoc pstatus
									          );

/// Set Time Offset

/// Use this function to set the camera's Time Offset value.  This will be the number of seconds to offset the IRIG time value by, multiplied by 10000.  A value of 1 is 100 microseconds.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetTimeOffset(long CameraID, ///< \copydoc cameraid
///     the new Time Offset value\n
									          int TimeOffset,
									          int* pStatus = NULL ///< \copydoc pstatus
									          );

/// Get Time Offset

/// Use this function to get the camera's Time Offset value.  This will be the number of seconds to offset the IRIG time value by, multiplied by 10000.  A value of 1 is 100 microseconds.\n
/// \return the camera's Time Offset value\n
MS_CAMERACONTROL_API int MS_GetTimeOffset(long CameraID, ///< \copydoc cameraid
									          int* pStatus = NULL ///< \copydoc pstatus
									          );

/// Set Timestamp Display Mode

/// Use this function to force, unforce, or disable the timestamp's month and day.
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetTimestampDisplayMode(long CameraID, ///< \copydoc cameraid
/// the new display mode for the timestamp\n
/// either c_TimestampModeNormal, c_TimestampModeNoDayAndMonth, or c_TimestampModeForcedDayAndMonth
int newMode,
													int* pStatus = NULL ///< \copydoc pstatus
													);
/// Set Force Timestamp Month

/// Use this function to force the timestamp's month to a specific value\n
/// The forced value will only be used if you use the MS_AVI_SetTimestampDisplayMode() function to set the mode to c_TimestampModeForcedDayAndMonth\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetForceTimestampMonth(long CameraID, ///< \copydoc cameraid
/// the value to force the timestamp month to
int newValue,
													int* pStatus = NULL ///< \copydoc pstatus
													);
/// Set Force Timestamp Day

/// Use this function to force the timestamp's day to a specific value\n
/// The forced value will only be used if you use the MS_AVI_SetTimestampDisplayMode() function to set the mode to c_TimestampModeForcedDayAndMonth\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetForceTimestampDay(long CameraID, ///< \copydoc cameraid
/// the value to force the timestamp day to
int newValue,
													int* pStatus = NULL ///< \copydoc pstatus
													);

/// Get Timestamp Display Mode

/// Use this function to check the timestamp display mode.  See MS_SetTimestampDisplayMode
/// \return the display mode for the timestamp\n
MS_CAMERACONTROL_API int MS_GetTimestampDisplayMode(long CameraID, ///< \copydoc cameraid
													int* pStatus = NULL ///< \copydoc pstatus
													);
/// Get Force Timestamp Month

/// Use this function to check the forced timestamp month.  See MS_SetForceTimestampMonth
/// \return the value to force the timestamp month to\n
MS_CAMERACONTROL_API int MS_GetForceTimestampMonth(long CameraID, ///< \copydoc cameraid
													int* pStatus = NULL ///< \copydoc pstatus
													);
/// Get Force Timestamp Day

/// Use this function to check the forced timestamp day.  See MS_SetForceTimestampDay
/// \return the value to force the timestamp day to\n
MS_CAMERACONTROL_API int MS_GetForceTimestampDay(long CameraID, ///< \copydoc cameraid
													int* pStatus = NULL ///< \copydoc pstatus
													);

/// Get Boost Value

/// Use this function to get the camera's boost value\n
/// Use the MS_CheckIfCameraHasBoostValue() function to check if this camera supports this function.\n
/// This function is only for MS70K and MS75K cameras.  This function will do nothing for other camera models.\n
/// For a list of allowed values, see \ref boostvalues\n
/// \return the camera's boost value\n
MS_CAMERACONTROL_API int MS_GetBoostValue(long CameraID, ///< \copydoc cameraid
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Set Boost Value

/// Use this function to set the camera's boost value\n
/// Use the MS_CheckIfCameraHasBoostValue() function to check if this camera supports this function.\n
/// This function is only for MS70K and MS75K cameras.  This function will do nothing for other camera models.\n
/// For a list of allowed values, see \ref boostvalues\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetBoostValue(long CameraID, ///< \copydoc cameraid
///     the camera's boost value\n
										  int boostValue,
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Get Camera Name

/// Use this function to get the camera's name\n
/// \return the camera's name\n
MS_CAMERACONTROL_API std::string MS_GetCameraName(long CameraID, ///< \copydoc cameraid
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Set Camera Name

/// Use this function to set the camera's name\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCameraName(long CameraID, ///< \copydoc cameraid
///     the camera's name\n
										  const char* CameraName,
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/*!
@}
*/

/*! \defgroup cameratypecheckingfunctions Camera Type-Checking Functions

These functions are used to check which features are available for the camera.

@{
*/


/// Get Camera Model String

/// Use this function to get the model type of the current camera, as a string value.\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_GetCameraModelString(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
												         int* pStatus = NULL ///< \copydoc pstatus
												         );


/// Check If Camera Has Color

/// Use this function to check if the camera uses the color settings\n
/// \return <b>true</b> if the camera uses the color settings\n
///   <b>false</b> if the camera does not use the color settings\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasColor(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Check If Camera Has Flash RAM

/// Use this function to check if the camera has a built-in Flash RAM\n
/// \return <b>true</b> if the camera has Flash RAM\n
///   <b>false</b> if the camera does not have Flash RAM\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasFlashRAM(long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Check If Camera Has Timeout

/// Use this function to check if the camera has a built-in \ref timeout feature\n
/// \return <b>true</b> if the camera has a \ref timeout feature\n
///   <b>false</b> if the camera does not have a \ref timeout feature\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasTimeout(long CameraID, ///< \copydoc cameraid
													 int* pStatus = NULL ///< \copydoc pstatus
													 );

/// Check If Camera Has Black Offset Value

/// Use this function to check if the camera uses the black offset value\n
/// \return <b>true</b> if the camera uses the black offset value\n
///   <b>false</b> if the camera does not use the black offset value\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasBlackOffsetValue(long CameraID, ///< \copydoc cameraid
															  int* pStatus = NULL ///< \copydoc pstatus
															  );

/// Check If Camera Has Temperature Monitor

/// Use this function to check if the camera has a built-in temperature monitor\n
/// \return <b>true</b> if the camera has a temperature monitor\n
///   <b>false</b> if the camera does not have a temperature monitor\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasTemperatureMonitor(long CameraID, ///< \copydoc cameraid
																int* pStatus = NULL ///< \copydoc pstatus
																);

/// Check If Camera Has ROI X and Y Offset Value

/// Use this function to check if the camera uses the Region of Interest X and Y offset value\n
/// \return <b>true</b> if the camera uses the Region of Interest X and Y offset value\n
///   <b>false</b> if the camera does not use the Region of Interest X and Y offset value\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasROIXandYOffsetValue(long CameraID, ///< \copydoc cameraid
															     int* pStatus = NULL ///< \copydoc pstatus
															     );

/// Check If Camera Has ESwitch

/// Use this function to check if the camera has the ESwitch input feature\n
/// \return <b>true</b> if the camera has the ESwitch input feature\n
///   <b>false</b> if the camera does not have the ESwitch input feature\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasESwitch(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Check If Camera Has RS422

/// Use this function to check if the camera has the RS422 input feature\n
/// \return <b>true</b> if the camera has the RS422 input feature\n
///   <b>false</b> if the camera does not have the RS422 input feature\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasRS422(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Check If Camera Has Binning

/// Use this function to check if the camera uses the \ref binning settings\n
/// \return <b>true</b> if the camera uses the \ref binning settings\n
///   <b>false</b> if the camera does not use the \ref binning settings\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasBinning(long CameraID, ///< \copydoc cameraid
													 int* pStatus = NULL ///< \copydoc pstatus
													 );

/// Check If Camera Has Trigger Type

/// Use this function to check if the specified trigger type is available in this camera\n
/// \return <b>true</b> if the \ref triggertypenumbers "Trigger Type" is available\n
///   <b>false</b> if the \ref triggertypenumbers "Trigger Type" is not available\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasTriggerType(long CameraID, ///< \copydoc cameraid
///  The \ref triggertypenumbers "Trigger Type" that you want to check is available in this camera
///  For a list of allowed values, see \ref triggertypevalues\n
														 int triggerType,
														 int* pStatus = NULL ///< \copydoc pstatus
														 );

/// Check If Camera Has Auto Exposure

/// Use this function to check if the camera has the auto-exposure feature\n
/// \return <b>true</b> if the camera has the auto-exposure feature\n
///   <b>false</b> if the camera does not have the auto-exposure feature\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasAutoExposure(long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Check If Auto Exposure Can Be Changed

/// Use this function to check if it is currently safe to change the auto-exposure settings.\n
/// The auto-exposure settings cannot be changed while capturing or downloading.\n
/// \return <b>true</b> if it is safe to change the auto-exposure settings\n
///   <b>false</b> if it is not safe to change the auto-exposure settings\n
MS_CAMERACONTROL_API bool MS_CheckIfAutoExposureCanBeChanged(long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Check If Auto Exposure Is Available In This Mode

/// Use this function to check if the auto-exposure feature is available in the currently selected capture mode.\n
/// The auto-exposure feature is not available in multi-speed or slave trigger mode.\n
/// \return <b>true</b> if the auto-exposure feature is available in this mode\n
///   <b>false</b> if the auto-exposure feature is not available in this mode\n
MS_CAMERACONTROL_API bool MS_CheckIfAutoExposureIsAvailableInThisMode(long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Check If Camera Has Preview Throttling

/// Use this function to check if the camera has the preview throttling feature\n
/// \return <b>true</b> if the camera has the preview throttling feature\n
///   <b>false</b> if the camera does not have the preview throttling feature\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasPreviewThrottling(long CameraID, ///< \copydoc cameraid
														        int* pStatus = NULL ///< \copydoc pstatus
														        );

/// Check If Camera Has Trigger Sensitivity

/// Use this function to check if the camera has the trigger sensitivity feature\n
/// \return <b>true</b> if the camera has the trigger sensitivity feature\n
///   <b>false</b> if the camera does not have the trigger sensitivity feature\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasTriggerSensitivity(long CameraID, ///< \copydoc cameraid
														        int* pStatus = NULL ///< \copydoc pstatus
														        );

/// Check If Camera Has Boost Value

/// Use this function to check if the camera uses the boost value\n
/// \return <b>true</b> if the camera uses the boost value\n
///   <b>false</b> if the camera does not use the boost value\n
MS_CAMERACONTROL_API bool MS_CheckIfCameraHasBoostValue(long CameraID, ///< \copydoc cameraid
														int* pStatus = NULL ///< \copydoc pstatus
														);



/*!
@}
*/

/*! \defgroup cameraboundscheckingfunctions Camera Bounds-Checking Functions

These functions are used to calculate the minimum and maximum allowed values for the camera's settings, and other related values or restrictions.

@{
*/


/// Calculate Min Capture Speed

/// Use this function to calculate the minimum possible capture speed for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The capture speed is measured in Frames Per Second.\n
/// This is for the value StructBasicCaptureSettings::CaptureSpeed\n
/// \return the minimum possible capture speed for this camera.\n
MS_CAMERACONTROL_API int MS_CalculateMinCaptureSpeed (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Max Capture Speed

/// Use this function to calculate the maximum possible capture speed for this camera at the specified image size.\n
/// Smaller image heights will result in higher maximum capture speeds.\n
/// The capture speed is measured in Frames Per Second.\n
/// This is for the value StructBasicCaptureSettings::CaptureSpeed\n
/// \return the maximum possible capture speed for this camera at the specified image size\n
MS_CAMERACONTROL_API int MS_CalculateMaxCaptureSpeed (long CameraID, ///< \copydoc cameraid
///     the image width that you want to calculate the maximum capture speed for\n
													  int ImageWidthBeforeBinning,
///     the image height that you want to calculate the maximum capture speed for\n
													  int ImageHeightBeforeBinning,
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Default Capture Speed

/// Use this function to calculate the default capture speed for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The capture speed is measured in Frames Per Second.\n
/// This is for the value StructBasicCaptureSettings::CaptureSpeed\n
/// \return the default capture speed for this camera.\n
MS_CAMERACONTROL_API int MS_CalculateDefaultCaptureSpeed (long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Calculate Min Download Speed

/// Use this function to calculate the minimum possible download speed for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The download speed is measured in Frames Per Second.\n
/// This is for the value StructDownloadSetting::DownloadSpeed and StructAutoDownloadSettings::AutoDownloadSpeed\n
/// \return the minimum possible download speed for this camera.\n
MS_CAMERACONTROL_API int MS_CalculateMinDownloadSpeed(long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Max Download Speed

/// Use this function to calculate the maximum possible download speed for this camera at the specified image size.\n
/// Smaller image heights will result in higher maximum download speeds.\n
/// The download speed is measured in Frames Per Second.\n
/// This is for the value StructDownloadSettings::DownloadSpeed and StructAutoDownloadSettings::AutoDownloadSpeed\n
/// \return the maximum possible download speed for this camera at the specified image size.\n
MS_CAMERACONTROL_API int MS_CalculateMaxDownloadSpeed(long CameraID, ///< \copydoc cameraid
///     the image width that you want to calculate the maximum download speed for\n
													  int ImageWidthAfterBinning,
///     the image height that you want to calculate the maximum download speed for\n
													  int ImageHeightAfterBinning,
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Min Exposure Time

/// Use this function to calculate the minimum possible exposure time for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The exposure time is measured in microseconds.\n
/// This is for the value StructBasicCaptureSettings::ExposureTime\n
/// \return the minimum possible exposure time for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinExposureTime (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Max Exposure Time

/// Use this function to calculate the maximum possible exposure time for this camera at the specified capture speed.\n
/// Lower capture speeds will result in higher maximum exposure times.\n
/// The exposure time is measured in microseconds.\n
/// This is for the value StructBasicCaptureSettings::ExposureTime\n
/// \return the maximum possible exposure time for this camera at the specified capture speed\n
MS_CAMERACONTROL_API int MS_CalculateMaxExposureTime (long CameraID, ///< \copydoc cameraid
///     the capture speed that you want to calculate the maximum exposure time for\n
													  int CaptureSpeed,
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Default Exposure Time

/// Use this function to calculate the default exposure time for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The exposure time is measured in microseconds.\n
/// This is for the value StructBasicCaptureSettings::ExposureTime\n
/// \return the default exposure time for this camera\n
MS_CAMERACONTROL_API int MS_CalculateDefaultExposureTime (long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Calculate Min Gain Value

/// Use this function to calculate the minimum possible gain value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The gain value is the raw value sent to the camera, and does not have any units.\n
/// This is for the value StructBasicCaptureSettings::GainValue\n
/// \return the minimum possible gain value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinGainValue    (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Max Gain Value

/// Use this function to calculate the maximum possible gain value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The gain value is the raw value sent to the camera, and does not have any units.\n
/// This is for the value StructBasicCaptureSettings::GainValue\n
/// \return the maximum possible gain value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMaxGainValue    (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Default Gain Value

/// Use this function to calculate the default gain value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The gain value is the raw value sent to the camera, and does not have any units.\n
/// This is for the value StructBasicCaptureSettings::GainValue\n
/// \return the default gain value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateDefaultGainValue    (long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Calculate Min Trigger Sensitivity

/// Use this function to calculate the minimum possible trigger sensitivity value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The trigger sensitivity value is the raw value sent to the camera, and does not have any units.\n
/// Use the function MS_AdjustTriggerSensitivityFromRawValueToMilliseconds() to convert this raw value used by the camera into the number of milliseconds for the delay.\n
/// Use the function MS_AdjustTriggerSensitivityFromMillisecondsToRawValue() to convert the desired number of milliseconds for the delay into the raw value used by the camera.\n
/// This is for the value StructAdvancedCaptureSettings::TriggerSensitivity\n
/// \return the minimum possible trigger sensitivity value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinTriggerSensitivity(long CameraID, ///< \copydoc cameraid
													       int* pStatus = NULL ///< \copydoc pstatus
													       );

/// Calculate Max Trigger Sensitivity

/// Use this function to calculate the maximum possible trigger sensitivity value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The trigger sensitivity value is the raw value sent to the camera, and does not have any units.\n
/// Use the function MS_AdjustTriggerSensitivityFromRawValueToMilliseconds() to convert this raw value used by the camera into the number of milliseconds for the delay.\n
/// Use the function MS_AdjustTriggerSensitivityFromMillisecondsToRawValue() to convert the desired number of milliseconds for the delay into the raw value used by the camera.\n
/// This is for the value StructAdvancedCaptureSettings::TriggerSensitivity\n
/// \return the maximum possible trigger sensitivity value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMaxTriggerSensitivity(long CameraID, ///< \copydoc cameraid
													 int* pStatus = NULL ///< \copydoc pstatus
													 );

/// Calculate Min Black Offset Value

/// Use this function to calculate the minimum possible black offset value for this camera.\n
/// Use the MS_CheckIfCameraHasBlackOffsetValue() function to check if this camera supports this function.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The black offset value is the raw value used by the software, and does not have any units.\n
/// \return the minimum possible black offset value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinBlackOffsetValue  (long CameraID, ///< \copydoc cameraid
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Calculate Max Black Offset Value

/// Use this function to calculate the maximum possible black offset value for this camera.\n
/// Use the MS_CheckIfCameraHasBlackOffsetValue() function to check if this camera supports this function.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The black offset value is the raw value used by the software, and does not have any units.\n
/// \return the maximum possible black offset value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMaxBlackOffsetValue  (long CameraID, ///< \copydoc cameraid
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Calculate Default Black Offset Value

/// Use this function to calculate the default black offset value for this camera.\n
/// Use the MS_CheckIfCameraHasBlackOffsetValue() function to check if this camera supports this function.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The black offset value is the raw value used by the software, and does not have any units.\n
/// \return the default black offset value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateDefaultBlackOffsetValue  (long CameraID, ///< \copydoc cameraid
															   int* pStatus = NULL ///< \copydoc pstatus
															   );

/// Calculate Min Intensity

/// Use this function to calculate the minimum possible intensity value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The intensity value is the raw value used by the software, and does not have any units.\n
/// This is for the value StructColorSettings::BayerIntensity, which is only used when StructColorSettings::DisplayMode is set to ::c_ColorModeGamma\n
/// \return the minimum possible intensity value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinIntensity    (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Max Intensity

/// Use this function to calculate the maximum possible intensity value for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The intensity value is the raw value used by the software, and does not have any units.\n
/// This is for the value StructColorSettings::BayerIntensity, which is only used when StructColorSettings::DisplayMode is set to ::c_ColorModeGamma\n
/// \return the maximum possible intensity value for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMaxIntensity    (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Min Image Width

/// Use this function to calculate the minimum possible image width for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The image width is measured in pixels.\n
/// This is for the NewImageWidth value passed to MS_ChangeImageSize()\n
/// \return the minimum possible image width for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinImageWidth   (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );

/// Calculate Max Image Width

/// Use this function to calculate the maximum possible image width for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The image width is measured in pixels.\n
/// This is for the NewImageWidth value passed to MS_ChangeImageSize()\n
/// \return the maximum possible image width for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMaxImageWidth   (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );




/// Calculate Min Image Height

/// Use this function to calculate the minimum possible image height for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The image height is measured in pixels.\n
/// This is for the NewImageHeight value passed to MS_ChangeImageSize()\n
/// \return the minimum possible image height for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMinImageHeight  (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );




/// Calculate Max Image Height

/// Use this function to calculate the maximum possible image height for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// The image height is measured in pixels.\n
/// This is for the NewImageHeight value passed to MS_ChangeImageSize()\n
/// \return the maximum possible image height for this camera\n
MS_CAMERACONTROL_API int MS_CalculateMaxImageHeight  (long CameraID, ///< \copydoc cameraid
													  int* pStatus = NULL ///< \copydoc pstatus
													  );



/// Calculate Image Width Rounding Value

/// Use this function to calculate the value that the image width must be a multiple of, for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// If the NewImageWidth value passed to MS_ChangeImageSize() is not a multiple of this value, then it will be rounded down to the next value that is.\n
/// \return the value that the image width must be a multiple of, for this camera\n
MS_CAMERACONTROL_API int MS_CalculateImageWidthRoundingValue (long CameraID, ///< \copydoc cameraid
															  int* pStatus = NULL ///< \copydoc pstatus
															  );

/// Calculate Image Height Rounding Value

/// Use this function to calculate the value that the image height must be a multiple of, for this camera.\n
/// This value will be a constant, and will not depend on any other settings.\n
/// If the NewImageHeight value passed to MS_ChangeImageSize() is not a multiple of this value, then it will be rounded down to the next value that is.\n
/// \return the value that the image height must be a multiple of, for this camera\n
MS_CAMERACONTROL_API int MS_CalculateImageHeightRoundingValue(long CameraID, ///< \copydoc cameraid
															  int* pStatus = NULL ///< \copydoc pstatus
															  );

/// Calculate Image Width Rounding Value With Binning

/// Use this function to calculate the value that the image width must be a multiple of, for this camera, when binning is enabled.\n
/// This value will depend only on the binning mode.\n
/// If the NewImageWidth value passed to MS_ChangeImageSize() is not a multiple of this value, then it will be rounded down to the next value that is.\n
/// \return the value that the image width must be a multiple of, for this camera\n
MS_CAMERACONTROL_API int MS_CalculateImageWidthRoundingValueWithBinning (long CameraID, ///< \copydoc cameraid
															  int* pStatus = NULL ///< \copydoc pstatus
															  );

/// Calculate Image Height Rounding Value With Binning

/// Use this function to calculate the value that the image height must be a multiple of, for this camera, when binning is enabled.\n
/// This value will depend only on the binning mode.\n
/// If the NewImageHeight value passed to MS_ChangeImageSize() is not a multiple of this value, then it will be rounded down to the next value that is.\n
/// \return the value that the image height must be a multiple of, for this camera\n
MS_CAMERACONTROL_API int MS_CalculateImageHeightRoundingValueWithBinning(long CameraID, ///< \copydoc cameraid
															  int* pStatus = NULL ///< \copydoc pstatus
															  );

/// Calculate Total Frames In Camera RAM

/// Use this function to calculate the number of frames in camera RAM, at the current image size.\n
/// Lower image sizes will result in a higher number of frames in camera RAM.\n
/// \return the number of frames in camera RAM, at the current image size\n
MS_CAMERACONTROL_API long MS_CalculateTotalFramesInCameraRAM(long CameraID, ///< \copydoc cameraid
															 int* pStatus = NULL ///< \copydoc pstatus
															 );

/// Calculate Max Preview Image Size

/// Use this function to calculate the size of the buffer that the camera uses to send the preview frame to the PC while a capture is in progress.\n
/// This value is measured in pixels.\n
/// If the requested image size is to large to fit in this buffer, then the width and height of the preview images will be cut in half, so that they will fit in the buffer.\n
/// When the images are downloaded from camera RAM, they will be downloaded at full resolution.\n
/// Only the preview images sent to the PC while the capture is in progress will be affected by this limited buffer size.\n
/// To calculate if an image size will be able to use a full-sized preview, multiply the image width by the image height, and compare the result to this value.\n
/// \return the size of the buffer that the camera uses to send the preview frame to the PC while a capture is in progress\n
MS_CAMERACONTROL_API double MS_CalculateMaxPreviewImageSize(long CameraID, ///< \copydoc cameraid
															int* pStatus = NULL ///< \copydoc pstatus
															);

/// Adjust Trigger Sensitivity From Milliseconds To Raw Value

/// Use this function to convert the desired number of milliseconds for the trigger delay into the raw TriggerSensitivity value used by the camera.\n
/// This is for the value StructAdvancedCaptureSettings::TriggerSensitivity\n
/// \return the raw TriggerSensitivity value used by the camera\n
MS_CAMERACONTROL_API double MS_AdjustTriggerSensitivityFromMillisecondsToRawValue(long CameraID, ///< \copydoc cameraid
///     the desired number of milliseconds for the trigger delay\n
																			double Value,
																			int* pStatus = NULL ///< \copydoc pstatus
																			);

/// Adjust Trigger Sensitivity From Raw Value To Milliseconds

/// Use this function to convert the raw TriggerSensitivity value used by the camera into the number of milliseconds for the trigger delay.\n
/// This is for the value StructAdvancedCaptureSettings::TriggerSensitivity\n
/// \return the number of milliseconds for the trigger delay\n
MS_CAMERACONTROL_API double MS_AdjustTriggerSensitivityFromRawValueToMilliseconds(long CameraID, ///< \copydoc cameraid
///     the raw TriggerSensitivity value used by the camera\n
																			double Value,
																			int* pStatus = NULL ///< \copydoc pstatus
																			);

/// Get Auto-Exposure Limits

/// Use this function to get the limits of various auto-exposure paramaters for the current image size and capture speed.
/// \return a struct containing the limits of various auto-exposure parameters
MS_CAMERACONTROL_API AutoExposureLimits MS_GetAutoExposureLimits(long  CameraID,	///< \copydoc cameraid
																	int *pStatus = NULL	///< \copydoc pstatus
																	);
/// Get Auto-Exposure Default Values

/// Use this function to get the default values of the auto-exposure settings for the current image size and capture speed.
/// \return a struct containing the default auto-exposure parameters for the current image size and capture rate
MS_CAMERACONTROL_API StructAutoExposureSettings MS_GetAutoExposureDefaults(long  CameraID,	///< \copydoc cameraid
																			int *pStatus = NULL	///< \copydoc pstatus
																			);
/// Calculate Limits for Auto-Exposure Target X Coordinate

/// Use this function to calculate the minimum and maximum X coordinate of the auto-expsoure window for the given image width and auto-exposure window width
/// \return a struct containing the minimum and maximum value for the auto-exposure window x-coordinate\n
MS_CAMERACONTROL_API RangeInt MS_CalculateAutoExposureTargetXLimit(long CameraID,	///< \copydoc cameraid
/// the image width to calculate the value for\n
																	int ImageWidth, 
/// the auto-exposure window width to calculate the value for\n
																	int  WindowWidth, 
																	int *pStatus = NULL	///< \copydoc pstatus
																	);
/// Calculate Limits for Auto-Exposure Target Y Coordinate

/// Use this function to calculate the minimum and maximum Y coordinate for the auto-exposure window for the given image height and auto-exposure window height
/// \return a struct containing the minimum and maximum value for the auto-exposure window y-coordinate\n
MS_CAMERACONTROL_API RangeInt MS_CalculateAutoExposureTargetYLimit(long CameraID,	///< \copydoc cameraid
/// the image height to calculate the value for\n
																	int ImageHeight, 
/// the auto-exposure window height to calculate the value for\n
																	int  WindowHeight, 
																	int *pStatus = NULL	///< \copydoc pstatus
																	);




/*!
@}
*/

/*! \defgroup cameramodechangingfunctions Camera Mode Changing Functions

These functions are used to change the camera's mode, or to change other settings that can only be changed when the camera is in \ref stopmode .

@{
*/

/// Change Image Size

/// Use this function to change the camera's current image size.\n
/// This is the image size that will be used when capturing frames to the camera or when downloading frames from the camera.\n
/// Calling this function will automatically reallocate the DLL's internal image buffers to use the new image size.\n
/// Use the following functions to check the allowed values for NewImageWidth and NewImageHeight:\n
/// MS_CalculateMinImageWidth()\n
/// MS_CalculateMaxImageWidth()\n
/// MS_CalculateMinImageHeight()\n
/// MS_CalculateMaxImageHeight()\n
/// MS_CalculateImageWidthRoundingValue()\n
/// MS_CalculateImageHeightRoundingValue()\n
/// \attention If you attempt to download at a different image size than the size the data was captured at, the downloaded data will be scrambled\n
/// If you attempt to access the StructBufferStatus::ImageBuffers while changing the image size, the software may crash!\n
/// Changing the capture mode will automatically change the image size.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ChangeImageSize(long CameraID, ///< \copydoc cameraid
///     the image width to change to\n
											int NewImageWidth,
///     the image height to change to\n
											int NewImageHeight,
											int* pStatus = NULL ///< \copydoc pstatus
											);

/// Set Allocated Memory Size

/// Use this function to adjust the number of megabytes that have been reserved for the DLL's internal image buffers.\n
/// The total amount of RAM used by the DLL will be slightly more than this value, since the image buffers aren't the only thing the DLL needs to reserve memory for.\n
/// The size of the DLL's internal buffers determines how many frames can be stored in the StructBufferStatus::ImageBuffers.\n
/// The default value is 80% of the RAM that is available when the DLL is initialized.\n
/// \return the new amount of memory allocated - this might not be exactly the same value as MegaBytesToAllocate\n
MS_CAMERACONTROL_API float MS_SetAllocatedMemorySize(long CameraID, ///< \copydoc cameraid
///     the number of megabytes of RAM to allocate\n
													 long MegaBytesToAllocate,
													 int* pStatus = NULL ///< \copydoc pstatus
													 );

/// Clear Buffers

/// Use this function to clear all of the images in the StructBufferStatus::ImageBuffers, setting them to all black.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ClearBuffers(long CameraID, ///< \copydoc cameraid
										 int* pStatus = NULL ///< \copydoc pstatus
										 );

/// Emergency Stop

/// Use this function to send an emergency stop command to the camera, which will return the camera to \ref stopmode no matter what mode it is currently in.\n
/// \attention This function should only be used in emergency situations where you must stop the camera immediately, without going through the proper procedure to use MS_StopCaptureOrDownload().\n
/// For normal use, you should use MS_StopCaptureOrDownload(), because the MS_EmergencyStop() function may corrupt image data.
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_EmergencyStop(long CameraID, ///< \copydoc cameraid
										  int* pStatus = NULL ///< \copydoc pstatus
										  );

/// Clear Camera RAM

/// Use this function to clear the contents of the camera's internal RAM.\n
/// This process will take several seconds, but this function will return immediately.  A callback function will report the clear progress.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ClearCameraRAM(long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/// Do Quick Recalibrate

/// Use this function to do a quick recalibration of the camera's sensor.\n
/// If you change the capture speed or exposure time while a capture is in progress, the image quality will be slightly reduced until the camera's sensor is recalibrated.\n
/// Starting a new capture will automatically recalibrate the camera's sensor.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_DoQuickRecalibrate(long CameraID, ///< \copydoc cameraid
											   int* pStatus = NULL ///< \copydoc pstatus
											   );

/// Start Capture Or Download

/// Use this function to start a capture or download.\n
/// StructCameraStatus::CameraMode and StructCameraStatus::TriggerType will determine which mode the camera will be started in\n
/// Before starting the capture or download, you must select the camera mode you want.\n
/// \copydoc functionstoswitchcameramodes
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_StartCaptureOrDownload(long CameraID, ///< \copydoc cameraid
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Stop Capture Or Download

/// Use this function to stop the current capture or download.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_StopCaptureOrDownload(long CameraID, ///< \copydoc cameraid
												  int* pStatus = NULL ///< \copydoc pstatus
												  );

/// Start Preview

/// If StructCameraStatus::CameraMode is set to ::c_CameraModeDownloadToPC, and the camera is idle, then you can use this function to start the download preview.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_StartPreview(long CameraID, ///< \copydoc cameraid
///     If this is set to <b>true</b>, then the preview will start from AlternatePreviewPos.\n
///     If this is set to <b>false</b>, then the preview will start from the current preview position, which is StructPreviewStatus::UpdatePreviewPicPos\n
										 bool UseAlternatePreviewPos = false,
///     This is the frame number that you want the download preview to start at.\n
///     If UseAlternatePreviewPos is set to <b>false</b>, then this value will be ignored.\n
										 int AlternatePreviewPos = 0,
										 int* pStatus = NULL ///< \copydoc pstatus
										 );

/// Stop Preview

/// Use this function to stop the download preview, and return the camera to idle mode.\n
/// This function will be called automatically if you call MS_StartCaptureOrDownload() to start a download,
///  or if you call MS_ExitDownloadModeAndReturnToPreviousCaptureMode() to exit download mode.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_StopPreview (long CameraID, ///< \copydoc cameraid
										 int* pStatus = NULL ///< \copydoc pstatus
										 );

/// Pause Download

/// If a download is in progress, you can use this function to pause the download.\n
/// You can safely review the frames that have already been downloaded to PC RAM, while the download is paused.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_PauseDownload (long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/// Resume Download

/// Use this function to resume the download, after you have paused it.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ResumeDownload(long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/// Switch To Capture Mode Continuous

/// Use this function to set the camera to \ref continuousmode, and to prepare the DLL to start a continuous capture to camera RAM.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SwitchToCaptureModeContinuous(long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Switch To Capture Mode By Trigger

/// Use this function to set the camera to \ref triggermode, and to prepare the DLL to start a triggered capture to camera RAM.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SwitchToCaptureModeByTrigger(long CameraID, ///< \copydoc cameraid
///     This is the type of trigger that the camera will wait for, when the capture is started.\n
/// For a list of allowed values, see \ref triggertypenumbers\n
														 int TriggerType,
														 int* pStatus = NULL ///< \copydoc pstatus
														 );

/// Switch To Download To PC Mode

/// Use this function to set the camera to \ref downloadtopcmode, and to prepare the DLL to download from camera RAM to PC RAM.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SwitchToDownloadToPCMode(long CameraID, ///< \copydoc cameraid
													 int* pStatus = NULL ///< \copydoc pstatus
													 );

/// Exit Download Mode And Return To Previous Capture Mode

/// Use this function to switch the camera from \ref downloadtopcmode to whatever mode it was in before entering download mode,
///  and to prepare the DLL to do a capture in the most recently used capture mode.\n
/// It is safe to switch directly from download mode to a different capture mode using either MS_SwitchToCaptureModeContinuous() or MS_SwitchToCaptureModeByTrigger().
///  You don't need to call this function first.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ExitDownloadModeAndReturnToPreviousCaptureMode(long CameraID, ///< \copydoc cameraid
																		   int* pStatus = NULL ///< \copydoc pstatus
																		   );

/// Set Update Preview Pic Pos

/// Use this function to select which preview frame you want to be displayed next.\n
/// If the camera is currently not in \ref downloadpreviewmode, then the preview frame won't be updated until the camera enters \ref downloadpreviewmode.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetUpdatePreviewPicPos(long CameraID, ///< \copydoc cameraid
///     This is the frame number of the preview frame that you want to display next\n
												   int NewUpdatePreviewPicPos,
												   int* pStatus = NULL ///< \copydoc pstatus
												   );

/// Refresh Preview Pic

/// Use this function to make the camera resend the most recently sent preview frame, if the camera is in \ref downloadpreviewmode.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_RefreshPreviewPic(long CameraID, ///< \copydoc cameraid
											  int* pStatus = NULL ///< \copydoc pstatus
											  );

/// Check If Preview Pic Needs Updating

/// Use this function to check if the camera has sent the most recently requested preview frame yet.\n
/// This function will return <b>true</b> if the DLL is still waiting for the camera to send the preview frame.\n
/// This function will return <b>false</b> if the DLL has already received the preview frame from the camera.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API bool MS_CheckIfPreviewPicNeedsUpdating(long CameraID, ///< \copydoc cameraid
															int* pStatus = NULL ///< \copydoc pstatus
															);

/// Check If Download Speed Is Locked

/// Use this function to check if the DLL is currently preventing the download speed from being increased, in order to prevent the gigabit overload from exceeding its limit.\n
/// While the download speed is locked, it can be manually decreased, but it cannot be manually increased.\n
/// This function will return <b>true</b> if the download speed is currently locked.\n
/// This function will return <b>false</b> if the download speed is currently unlocked.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API bool MS_CheckIfDownloadSpeedIsLocked(long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/*!
@}
*/

/*! \defgroup filewritingfunctions File Writing Functions

These functions are used to write image files to the PC's hard drive.

@{
*/





/// Save To AVI

/// Use this function to save a range of frames from the StructBufferStatus::ImageBuffers to an AVI file.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SaveToAVI(long CameraID, ///< \copydoc cameraid
///     This is the filename of the AVI file that you want to save to.\n
									  const char* FileName,
///     This is the frame number of the first frame that you want to save from the StructBufferStatus::ImageBuffers.\n
									  int FirstFrame,
///     This is the frame number of the last frame that you want to save from the StructBufferStatus::ImageBuffers.\n
///     If this number is less than FirstFrame, then the save process will start from FirstFrame, then continue to the last frame in the StructBufferStatus::ImageBuffers,
///      then wrap around to the first frame in the image buffers, then continue to the end frame.\n
									  int LastFrame,
///     If this is <b>true</b>, then the saved AVI file will be compressed.\n
///     If this is <b>false</b>, then the saved AVI file will not be compressed.\n
									  bool IsCompressed,
///     If this is <b>true</b>, then the DLL will attempt to open the Mega Speed AVI Player to open the saved AVI file once the saving process is finished.\n
///     If this is <b>false</b>, then the DLL will not attempt to open the Mega Speed AVI Player to open the saved AVI file once the saving process is finished.\n
									  bool OpenTheFile,
									  int* pStatus = NULL ///< \copydoc pstatus
									  );



/// Save To Image File

/// Use this function to save a range of frames from the StructBufferStatus::ImageBuffers to an Image file.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SaveToImageFile(long CameraID, ///< \copydoc cameraid
///     This is the filename of the image file that you want to save to.\n
											const char* FileName,
///     This is the frame number of the first frame that you want to save from the StructBufferStatus::ImageBuffers.\n
											int FirstFrame,
///     This is the frame number of the last frame that you want to save from the StructBufferStatus::ImageBuffers.\n
///     If this number is less than FirstFrame, then the save process will start from FirstFrame, then continue to the last frame in the StructBufferStatus::ImageBuffers,
///      then wrap around to the first frame in the image buffers, then continue to the end frame.\n
											int LastFrame,
///     This is the type of image file to save to.\n
/// For a list of allowed values, see \ref imagefiletypes\n
											int ImageType,
///     If this is <b>true</b>, then the DLL will attempt to open the Mega Speed Image Viewer to open the saved image files once the saving process is finished.\n
///     If this is <b>false</b>, then the DLL will not attempt to open the Mega Speed Image Viewer to open the saved image files once the saving process is finished.\n
											bool OpenTheFile,
											int* pStatus = NULL ///< \copydoc pstatus
											);

/// Set Download Destination To PC RAM

/// Use this function to change StructDownloadSettings::DestFileType to ::c_DownloadToRAM, and prepare the DLL to download to PC RAM\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetDownloadDestinationToPCRAM(long CameraID, ///< \copydoc cameraid
														  int* pStatus = NULL ///< \copydoc pstatus
														  );


/// Set Download Destination To BMP File

/// Use this function to change StructDownloadSettings::DestFileType to ::c_DownloadToBMP, and prepare the DLL to download to a series of BMP files\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetDownloadDestinationToBMPFile(long CameraID, ///< \copydoc cameraid
///     This is the filename of the image file that you want to save to.\n
															const char* FileName,
															int* pStatus = NULL ///< \copydoc pstatus
															);


/// Set Download Destination To JPG File

/// Use this function to change StructDownloadSettings::DestFileType to ::c_DownloadToJPG, and prepare the DLL to download to a series of JPG files\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetDownloadDestinationToJPGFile(long CameraID, ///< \copydoc cameraid
///     This is the filename of the image file that you want to save to.\n
															const char* FileName,
															int* pStatus = NULL ///< \copydoc pstatus
															);


/// Set Download Destination To AVI File

/// Use this function to change StructDownloadSettings::DestFileType to ::c_DownloadToAVI, and prepare the DLL to download to an uncompressed AVI file\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetDownloadDestinationToAVIFile(long CameraID, ///< \copydoc cameraid
///     This is the filename of the AVI file that you want to save to.\n
															const char* FileName,
															int* pStatus = NULL ///< \copydoc pstatus
															);


/// Set Download Destination To AVI File Compressed

/// Use this function to change StructDownloadSettings::DestFileType to ::c_DownloadToCompressedAVI, and prepare the DLL to download to a compressed AVI file\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetDownloadDestinationToAVIFileCompressed(long CameraID, ///< \copydoc cameraid
///     This is the filename of the AVI file that you want to save to.\n
																	  const char* FileName,
																	  int* pStatus = NULL ///< \copydoc pstatus
																	  );


/// Write One BMP From Buffer

/// Use this function to save a frame from the StructBufferStatus::ImageBuffers to the PC hard drive as a bitmap file, in the current DisplayMode.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_WriteOneBMPFromBuffer(long CameraID, ///< \copydoc cameraid
///     This is the filename of the bitmap file that you want to save the image to.\n
												  const char* FileName,
///     This is the number of the frame in StructBufferStatus::ImageBuffers that you want to save to the bitmap file.\n
												  long FrameNum,
												  int* pStatus = NULL ///< \copydoc pstatus
												  );

/// Open Advanced Compression Settings Dlg

/// Use this function to open the dialog that lets you configure the \ref indeo codec's advanced settings - to enable or disable the "Quick Compress" option.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_OpenAdvancedCompressionSettingsDlg(int* pStatus = NULL ///< \copydoc pstatus
												  );

/// Pause Overload

/// When the camera is finished sending frames to the PC, when a download to an AVI file is finished,
///  the PC will still need to finish saving the rest of the frames from its overload buffer to the AVI file.\n
/// \return the value of *pStatus\n
/// Use this function to pause the overload processing.\n
MS_CAMERACONTROL_API int MS_PauseOverload (long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/// Resume Overload

/// Use this function to resume the overload processing, after it has been paused.\n
MS_CAMERACONTROL_API int MS_ResumeOverload(long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/// Cancel Overload

/// Use this function to cancel the overload processing.\n
/// This will prevent the remaining frames in the overload buffer from being saved to the AVI file.\n
MS_CAMERACONTROL_API int MS_CancelOverload(long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/// Cancel Export

/// Use this function to cancel the saving process started by MS_SaveToAVI() or MS_SaveToImageFile()\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_CancelExport  (long CameraID, ///< \copydoc cameraid
										   int* pStatus = NULL ///< \copydoc pstatus
										   );

/*!
@}
*/

/*! \defgroup imagebufferfunctions Image Buffer Functions

These functions are used to process images stored in the image buffers in PC RAM.

@{
*/

/// Do Post-Processing Black and White

/// This function will convert the requested frame from the StructBufferStatus::ImageBuffers into Black and White format, and then attach the overlay data onto the image.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeBW or ::c_ColorModeGamma, but it can safely be used in any display mode.\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
/// \return the pointer to the buffer\n
MS_CAMERACONTROL_API unsigned char* MS_DoPostProcessingBW       (long CameraID, ///< \copydoc cameraid
///     This is the frame number of the frame in the StructBufferStatus::ImageBuffers that you want to process.\n
																 long FrameNum,
																 int* pStatus = NULL ///< \copydoc pstatus
																 );

/// Do Post-Processing Color

/// This function will convert the requested frame from the StructBufferStatus::ImageBuffers into Color format, and then attach the overlay data onto the image.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeColor, but it can safely be used in any display mode.\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
/// \return the pointer to the buffer\n
MS_CAMERACONTROL_API unsigned long* MS_DoPostProcessingColor    (long CameraID, ///< \copydoc cameraid
///     This is the frame number of the frame in the StructBufferStatus::ImageBuffers that you want to process.\n
																 long FrameNum,
																 int* pStatus = NULL ///< \copydoc pstatus
																 );

/// Do Post-Processing Grayscale

/// This function will convert the requested frame from the StructBufferStatus::ImageBuffers into Grayscale format, and then attach the overlay data onto the image.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeGrayscale, but it can safely be used in any display mode.\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
/// \return the pointer to the buffer\n
MS_CAMERACONTROL_API unsigned char* MS_DoPostProcessingGrayscale(long CameraID, ///< \copydoc cameraid
///     This is the frame number of the frame in the StructBufferStatus::ImageBuffers that you want to process.\n
																 long FrameNum,
																 int* pStatus = NULL ///< \copydoc pstatus
																 );


/// Read Time Stamp From Frame

/// Use this function to read the embedded time stamp data from a frame in StructBufferStatus::ImageBuffers.\n
/// The data will be returned as a string with the format:\n
/// ("%02d/%02d %02d:%02d:%02d %03d.%01d", Time.wMonth, Time.wDay, Time.wHour, Time.wMinute, Time.wSecond, Time.wMilliseconds, Milliseconds.LowPart%10);\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_ReadTimeStampFromFrame(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the character array to update.\n
														   char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
														   int numChars,
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														   unsigned char* pImg,
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Read Capture Speed From Frame

/// Use this function to read the embedded capture speed data from a frame in StructBufferStatus::ImageBuffers.\n
/// The value returned is measured in frames per second.\n
/// \return the capture speed, in frames per second\n
MS_CAMERACONTROL_API int MS_ReadCaptureSpeedFromFrame(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
												      unsigned char* pImg,
												      int* pStatus = NULL ///< \copydoc pstatus
												      );

/// Read Exposure Time From Frame

/// Use this function to read the embedded exposure time data from a frame in StructBufferStatus::ImageBuffers.\n
/// The value returned is measured in milliseconds.\n
/// \return the exposure time, in milliseconds\n
MS_CAMERACONTROL_API int MS_ReadExposureTimeFromFrame(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
												      unsigned char* pImg,
												      int* pStatus = NULL ///< \copydoc pstatus
												      );

/// Read Camera Mode From Frame

/// Use this function to read the embedded camera mode data from a frame in StructBufferStatus::ImageBuffers.\n
/// The value returned has the same format as StructCameraStatus::CameraCurrentState.\n
/// \return the camera's capture mode, in the same format as StructCameraStatus::CameraCurrentState\n
MS_CAMERACONTROL_API int MS_ReadCameraModeFromFrame(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
												    unsigned char* pImg,
												    int* pStatus = NULL ///< \copydoc pstatus
												    );

/// Read Camera Temperature From Frame

/// Use this function to read the embedded camera temperature data from a frame in StructBufferStatus::ImageBuffers.\n
/// The value returned is measured in degrees Celsius.\n
/// \return the camera's temperature, in degrees Celsius\n
MS_CAMERACONTROL_API int MS_ReadCameraTemperatureFromFrame(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
												           unsigned char* pImg,
												           int* pStatus = NULL ///< \copydoc pstatus
												           );


/// Read RS422 Data From Frame

/// Use this function to read the embedded RS422 data from a frame in StructBufferStatus::ImageBuffers.\n
/// The data will be returned as a string of hexadecimal characters.\n
/// The length of the string will be determined by the number of RS422 data bytes, as specified by the MS_SetRS422DataBytes() function.\n
/// Each byte of data will be 2 hexadecimal characters.\n
/// Use the MS_CheckIfCameraHasRS422() function to check if this camera supports this function.\n
/// \return the value of pStatus\n
MS_CAMERACONTROL_API int MS_ReadRS422DataFromFrame(long CameraID, ///< \copydoc cameraid
///     This is the pointer to the character array to update.\n
															char* pString,
///     This is the size, in characters, of the character array to update.  If the returned string is longer than this, then the remaining characters will be cut off.\n
															int numChars,
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														   unsigned char* pImg,
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Get Color Image

/// This function will convert an image in StructBufferStatus::ImageBuffers from 8-bit raw data to 32-bit color, and store the result in one of the DLL's internal buffers.\n
/// The original image in StructBufferStatus::ImageBuffers will not be affected by this process.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeColor\n
/// This function returns a pointer to the processed frame\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
/// \return the pointer to the buffer\n
MS_CAMERACONTROL_API unsigned long* MS_GetColorImage      (long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														   unsigned char* pIn,
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Get Grayscale Image

/// This function will leave the image in 8-bit grayscale format, but will remove the bayer pattern noise from the image, and store the result in one of the DLL's internal buffers.\n
/// The original image in StructBufferStatus::ImageBuffers will not be affected by this process.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeGrayscale\n
/// This function returns a pointer to the processed frame\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
/// \return the pointer to the buffer\n
MS_CAMERACONTROL_API unsigned char* MS_GetGrayscaleImage  (long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														   unsigned char* pIn,
														   int* pStatus = NULL ///< \copydoc pstatus
														   );

/// Get Color Image

/// This function will convert an image in FrameBuffers from 8-bit raw data to 32-bit color, and store the result in a user-created buffer.\n
/// The original image in StructBufferStatus::ImageBuffers will not be affected by this process.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeColor\n
/// \attention You must manually allocate the buffer pOut before you call this function, and free this buffer when you are finished using it.\n
///            The size of this buffer must be StructCurrentImageSize.ImageWidthFromCamera * StructCurrentImageSize.ImageHeightFromCamera * 4, because each pixel will be 32 bits.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_GetColorImage                (long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														  unsigned char* pIn,
///     This is the pointer to the processed image.\n
														  unsigned long* pOut,
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Get Grayscale Image

/// This function will leave the image in 8-bit grayscale format, but will remove the bayer pattern noise from the image, and store the result in a user-created buffer.\n
/// The original image in StructBufferStatus::ImageBuffers will not be affected by this process.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeGrayscale\n
/// \attention You must manually allocate the buffer pOut before you call this function, and free this buffer when you are finished using it.\n
///            The size of this buffer must be StructCurrentImageSize.ImageWidthFromCamera * StructCurrentImageSize.ImageHeightFromCamera * 1, because each pixel will be 8 bits.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_GetGrayscaleImage            (long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														  unsigned char* pIn,
///     This is the pointer to the processed image.\n
														  unsigned char* pOut,
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Apply Gamma

/// This function will leave the image in 8-bit grayscale format, but will apply the gamma settings to the image, and store the result in one of the DLL's internal buffers.\n
/// The original image in StructBufferStatus::ImageBuffers will not be affected by this process.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeGamma\n
/// This function returns a pointer to the processed frame\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ApplyGamma                   (long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														  unsigned char* pIn,
														  int* pStatus = NULL ///< \copydoc pstatus
														  );

/// Apply Gamma

/// This function will leave the image in 8-bit grayscale format, but will apply the gamma settings to the image, and store the result in a user-created buffer.\n
/// The original image in StructBufferStatus::ImageBuffers will not be affected by this process.\n
/// This function is meant to be used when StructColorSettings::DisplayMode is set to ::c_ColorModeGamma\n
/// \attention You must manually allocate the buffer pOut before you call this function, and free this buffer when you are finished using it.\n
///            The size of this buffer must be StructCurrentImageSize.ImageWidthFromCamera * StructCurrentImageSize.ImageHeightFromCamera * 1, because each pixel will be 8 bits.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_ApplyGamma                   (long CameraID, ///< \copydoc cameraid
///     This is the pointer to the image buffer to process.\n
///     This should be set to either a frame from the StructBufferStatus::ImageBuffers, or the pImage pointer passed to one of the callback functions.\n
														  unsigned char* pIn,
///     This is the pointer to the processed image.\n
														  unsigned char* pOut,
														  int* pStatus = NULL ///< \copydoc pstatus
														  );



/*!
@}
*/

/*!
@}
*/

/***************************************************************************************************************************************/

/*! \defgroup callbackfunctions Callback Functions

This DLL provides several callback functions, to allow your software to respond immediately when certain events happen.

For most applications, you will not need to use these callback functions, since you can manually poll the DLL's status variables to get the same information.

This manual will assume that you are already familiar with how callback functions work.

In all of these callback functions, the first parameter is the CameraID.

If you do not plan to use these callback functions, then you do not need to initialize them.

If you plan to use any of these functions, then you need to initialize them after the CameraID has been initialized, by calling MS_InitializeCameraID()

The exception to this is MS_SetCallback_CheckPresetSettings() - this needs to be initialized after the call to MS_InitializeDLL(), but before the call to MS_InitializeCameraID().

\attention The DLL will wait for these callback functions to complete before it continues with what it was doing before.
Do not create callback functions that will take more than a few milliseconds to complete, or the DLL may freeze!!!

@{
*/


/// Set "Capture Start" Callback

/// This callback function is called whenever a capture or download is started, immediately after the start command has been sent to the camera.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_CaptureStart                        (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Capture Stop" Callback

/// This callback function is called whenever a capture or download is finished, immediately after the stop command has been sent to the camera.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_CaptureStop                         (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Auto-Download Setup" Callback

/// This callback function is called whenever the camera is about to start an automatic download, immediately after the automatic call to MS_SwitchToDownloadToPCMode().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_AutoDownloadSetup                   (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Auto-Download Start" Callback

/// This callback function is called whenever the camera is about to start an automatic download, immediately before the automatic call to MS_StartCaptureOrDownload().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_AutoDownloadStart                   (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Auto-Download Finished" Callback

/// This callback function is called whenever the camera is about to start an automatic download, approximately one second after the automatic call to ExitDownloadModeAndReturnToPreviousCaptureMode().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_AutoDownloadFinished                (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Download Speed Automatically Changed" Callback

/// This callback function is called whenever the download speed is automatically changed, immediately before the command to change the download speed is sent to the camera.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_DownloadSpeedAutomaticallyChanged   (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Download Speed Cannot Be Changed Now" Callback

/// This callback function is called whenever the download speed control is locked, immediately after it is locked.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_DownloadSpeedCannotBeChangedNow     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Download Speed Can Be Changed Now" Callback

/// This callback function is called whenever the download speed control is unlocked, immediately after it is unlocked.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_DownloadSpeedCanBeChangedNow        (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Acquired New Frame" Callback

/// This callback function is called every time a new frame is acquired from the camera, immediately after the DLL has finished writing the frame to the StructBufferStatus::ImageBuffers.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_AcquiredNewFrame                    (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Hard Drive Failed To Keep Up" Callback

/// This callback function is called when the hard drive fails to keep up with downloading to a file.  This should never happen, since the download speed is automatically throttled back to prevent this.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_HardDriveFailedToKeepUp             (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Automatically Changing Destination File" Callback

/// This function is called every time the destination file name is changed, when saving to the hard drive.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_AutomaticallyChangingDestinationFile(long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Finished Saving File" Callback

/// This function is caled when the DLL is finished saving to an AVI file or a series of image files - either from PC RAM or directly from the camera.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_FinishedSavingFile                  (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the filename of the file that the DLL finished saving to.\n The pointer temporary and should not be stored for later use.\n
																			 void (* callback)(long, const char*),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Failed Saving File" Callback

/// This callback function is called if the DLL fails to save to a file, for example, because there is no hard drive space left.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_FailedSavingFile                    (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the filename of the file that the DLL failed to save to.\n The pointer temporary and should not be stored for later use.\n
																			 void (* callback)(long, const char*),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Failed To Connect To Camera" Callback

/// This callback function is called if the DLL fails to connect to the camera, for example, because the IP address was invalid.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_FailedToConnectToCamera             (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is a message explaining why the connection failed.\n The pointer temporary and should not be stored for later use.\n
																			 void (* callback)(long, const char*),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Write To Log File" Callback

/// This callback function is called if the DLL has a message that it wants to be written to a log file.\n
/// The DLL will not write the message to the log file automatically, but will send the message in this callback function instead.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_WriteToLogFile                      (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is a message to write to the log file.\n The pointer temporary and should not be stored for later use.\n
																			 void (* callback)(long, const char*),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Show Message Box" Callback

/// This callback function is called if the DLL wants to display a message to the user, other than one of the error messages\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ShowMessageBox                      (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the message to display.\n The pointer temporary and should not be stored for later use.\n
/// The callback function's third parameter is type of icon to display in the message box, which will be one of the following values:\n
/// MB_ICONEXCLAMATION   An exclamation-point icon appears in the message box.\n
/// MB_ICONINFORMATION   An icon consisting of an "i" in a circle appears in the message box.\n
/// MB_ICONQUESTION   A question-mark icon appears in the message box.\n
/// MB_ICONSTOP   A stop-sign icon appears in the message box. \n
																			 void (* callback)(long, const char*, unsigned int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Update Save Range" Callback

/// This callback function is called when the DLL updates the range of frames that it will save from PC RAM, after a call to MS_SaveToAVI() or MS_SaveToImageFile().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_UpdateSaveRange                     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the number of frames that will be saved\n
																			 void (* callback)(long, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Update Save Progress" Callback

/// This callback function is called when the DLL updates the number of frames that have been saved from PC RAM, after a call to MS_SaveToAVI() or MS_SaveToImageFile().\n
/// This is updated approximately 10 times per second, not after each frame is saved to the file.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_UpdateSaveProgress                  (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the number of frames that have already been saved.\n
/// The callback function's third parameter is the total number of frames that will be saved.\n
																			 void (* callback)(long, int, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Update Clear Camera RAM Range" Callback

/// This callback function is called when the DLL updates the time required to clear camera RAM, after a call to MS_ClearCameraRAM().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_UpdateClearCameraRAMRange           (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the number of iterations required, where each iteration is 100 milliseconds\n
																			 void (* callback)(long, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Update Clear Camera RAM Progress" Callback

/// This callback function is called when the DLL updates the progress when clearing camera RAM, after a call to MS_ClearCameraRAM().\n
/// This is updated approximately 10 times per second.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_UpdateClearCameraRAMProgress        (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the number of iterations that have already passed.\n
/// The callback function's third parameter is the total number of iterations required, where each iteration is 100 milliseconds.\n
																			 void (* callback)(long, int, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Finished Clear Camera RAM" Callback

/// This callback function is called when the DLL finishes clearing camera RAM, after a call to MS_ClearCameraRAM().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_FinishedClearCameraRAM        (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Update Extract RS422 Data Range" Callback

/// This callback function is called when the DLL updates the total number of frames to extract RS422 data from, after a call to MS_ExtractRS422Data().\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_UpdateExtractRS422DataRange           (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the number of frames to extract RS422 data from\n
																			 void (* callback)(long, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Update Extract RS422 Data Progress" Callback

/// This callback function is called when the DLL updates the progress when extracting RS422 data, after a call to MS_ExtractRS422Data().\n
/// This is updated approximately 10 times per second.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_UpdateExtractRS422DataProgress        (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the number of frames that have already been processed.\n
/// The callback function's third parameter is the total number of frames that need to be processed.\n
																			 void (* callback)(long, int, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Begin Wait Cursor" Callback

/// This callback function is called whenever the DLL is about to start a process that will prevent it from accepting any more commands until it is finished, for example, MS_ChangeImageSize()\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_BeginWaitCursor                     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "End Wait Cursor" Callback

/// This callback function is called whenever the DLL is finished a process that prevented it from accepting any more commands until it is finished, for example, MS_ChangeImageSize()\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_EndWaitCursor                       (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Changing Image Size" Callback

/// This callback function is called whenever the DLL is changing the current image size, immediately before reallocating the StructBufferStatus::ImageBuffers to the new size\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ChangingImageSize                   (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Changing Capture Settings" Callback

/// This callback function is called whenever the DLL automatically changes the StructBasicCaptureSettings settings, immediately after changing the settings\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ChangingCaptureSettings             (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Clearing Buffers" Callback

/// This callback function is called whenever the DLL is clearing the StructBufferStatus::ImageBuffers, immediately after the buffers are cleared\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ClearingBuffers                     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Recalculate Zoom" Callback

/// This callback function is called whenever the DLL updates the values of StructCurrentImageSize.ImageWidthFromCamera and StructCurrentImageSize.ImageHeightFromCamera, immediately after updating these values.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_RecalculateZoom                     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Buffers Reallocated" Callback

/// This callback function is called whenever the DLL reallocates the StructBufferStatus::ImageBuffers, immediately after the buffers are reallocated.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_BuffersReallocated                  (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Found More Than One Camera" Callback

/// This callback function is called whenever the function MS_ConnectToAvailableCameraWithCallback() detects more than one camera.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_FoundMoreThanOneCamera              (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Received Preview Frame" Callback

/// This callback function is called whenever a preview frame is received from the camera, immediately after the preview frame has been written to the preview frame buffer.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ReceivedPreviewFrame                (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the pointer to the buffer where the preview frame was written.\n
/// \attention The pointer that is returned points to a buffer that is reserved internally by the DLL.  If you try to manually free this buffer, then the DLL will crash!\n
																			 void (* callback)(long, unsigned char*),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Polled AVI Save Overload" Callback

/// This callback function is called whenever the DLL has polled the number of frames written to the AVI file, during the overload processing.\n
/// This is called approximately 10 times per second.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_PolledAVISaveOverload               (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Polled Camera Connection" Callback

/// This callback function is called whenever the DLL has checked if the camera is connected\n
/// This is called approximately once per second.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_PolledCameraConnection              (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Camera Connected" Callback

/// This callback function is called whenever the DLL successfully connects to the camera, after it has been disconnected\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_CameraConnected                     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Camera Disconnected" Callback

/// This callback function is called whenever the DLL loses its connection to the camera, after it was successfully connected\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_CameraDisconnected                  (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Polled Camera Temperature" Callback

/// This callback function is called whenever the DLL polls the camera temperature.\n
/// This is called approximately once per second.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_PolledCameraTemperature             (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the camera's core temperature, in degrees Celsius.\n
/// The callback function's third parameter is the camera's board temperature, in degrees Celsius.\n
																			 void (* callback)(long, int, int),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Pre-Change Camera Mode" Callback

/// This callback function is called whenever the DLL changes the StructCameraStatus::CameraMode or StructCameraStatus::TriggerType, before any of the settings are updated.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_PreChangeCameraMode                 (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Post-Change Camera Mode" Callback

/// This callback function is called whenever the DLL changes the StructCameraStatus::CameraMode or StructCameraStatus::TriggerType, after all of the settings are updated.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_PostChangeCameraMode                (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Confirm Process Overload" Callback

/// This callback function is called whenever the DLL needs to check if you want to proceed with the overload processing.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ConfirmProcessOverload              (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the start frame number - this will always be 1.\n
/// The callback function's third parameter is the end frame number - this is the number of frames in the buffer that still need to be written.\n
/// If you don't want to process all of the frames, then you can set the second parameter to the number of frames that you want to process.\n
/// Return <b>true</b> if you want to proceed with the overload processing.\n
/// Return <b>false</b> if you do not want to proceed with the overload processing.\n
																			 bool (* callback)(long, int&, int&),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Check Preset Settings" Callback

/// This callback function is called whenever the DLL needs to check if you want to proceed with loading the preset settings, when the camera ID is initialized.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_CheckPresetSettings                 (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
/// The callback function's second parameter is the struct of the preset settings to load.\n
/// Return <b>true</b> if you want to proceed with loading the preset settings.\n
/// Return <b>false</b> if you do not want to proceed with loading the preset settings.\n
																			 bool (* callback)(long, StructPresetSettings),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Changed CameraStatus" Callback

/// This callback function is called whenever ::StructCameraStatus is changed.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ChangedCameraStatus                 (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Changed CurrentImageSize" Callback

/// This callback function is called whenever ::StructCurrentImageSize is changed.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ChangedCurrentImageSize             (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Changed AutoExposureSettings" Callback

/// This callback function is called whenever ::StructAutoExposureSettings is changed.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_ChangedAutoExposureSettings              (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/// Set "Cleanup CameraID" Callback

/// This callback function is called whenever the MS_CleanupCameraID() function is called.\n
/// \return the value of *pStatus\n
MS_CAMERACONTROL_API int MS_SetCallback_CleanupCameraID                     (long CameraID, ///< \copydoc cameraid
/// This is a pointer to the function that you want as the new callback function.\n
/// The callback function's first parameter is the CameraID value.\n
																			 void (* callback)(long),
																			 int* pStatus = NULL ///< \copydoc pstatus
																			 );

/*!
@}
*/

/***************************************************************************************************************************************/

/*! \defgroup genutilityfunctions Utility Functions

Other potentially useful functions

@{
*/


///Reads the embedded timestamp from a frame from a previously saved avi, and converts it to a string which is stored in Result
MS_CAMERACONTROL_API void MS_ReadTimeStampFromSavedFrame(
///Pointer to the image data the timestamp will be read from
														 const unsigned char *SrcImg,
///The width of the input frame
														 int Width, 
///The height of the input frame (Note: Height should <b>not</b> include the encoded data row.)
														 int Height, 
///The timestamp is internally stored as a day in the year (1-365|366) and converted to a month day format
///The leap year flag will cause February to be treated as either 28 or 29 days long.
														 bool LeapYear, 
///The result string is stored here, must not be NULL
														 char *Result, 
///Length of the result string buffer
														 int ResultLength
														 );

///Reads the embedded marker from a frame from a previously saved avi, and converts it to a string which is stored in Result
MS_CAMERACONTROL_API void MS_ReadMarkerFromSavedFrame(
///Pointer to the image data the timestamp will be read from
														 const unsigned char *SrcImg,
///The width of the input frame
														 int Width, 
///The height of the input frame (Note: Height should <b>not</b> include the encoded data row.)
														 int Height, 
///The result string is stored here, must not be NULL
														 char *Result, 
///Length of the result string buffer
														 int ResultLength
													  );

///Reads the embedded capture speed from a frame from a previously saved avi
/// \return The capture speed, in Frames per second
MS_CAMERACONTROL_API int MS_ReadCaptureSpeedFromSavedFrame(
///Pointer to the image data the timestamp will be read from
														 const unsigned char *SrcImg,
///The width of the input frame
														 int Width, 
///The height of the input frame (Note: Height should <b>not</b> include the encoded data row.)
														 int Height
														   );

///Reads the embedded exposure time from a frame from a previously saved avi
/// \return The exposure time, in microseconds
MS_CAMERACONTROL_API int MS_ReadExposureTimeFromSavedFrame(
///Pointer to the image data the timestamp will be read from
														 const unsigned char *SrcImg,
///The width of the input frame
														 int Width, 
///The height of the input frame (Note: Height should <b>not</b> include the encoded data row.)
														 int Height
														  );

/*!
@}
*/



/*! \defgroup cameramodes Camera Modes

This section of the manual describes the different modes that the camera can be in.\n
\n
\n
\copydoc cameramodevalues
\n
\copydoc triggertypevalues
\n
\n
The value StructCameraStatus::CameraCurrentState reports the mode that the camera is currently in.\n
\n
The value StructCameraStatus::CameraMode reports the state that the camera will be in the next time it receives a start command.\n
\n
\n
\copydoc functionstoswitchcameramodes
\n

@{
*/

/*! \defgroup continuousmode Continuous Mode

To set the camera to Continuous Mode, use the MS_SwitchToCaptureModeContinuous() function.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeContinuousCaptureToCameraRAM.\n
\n
Use the MS_StartCaptureOrDownload() function to start the capture, and use the MS_StopCaptureOrDownload() function to stop the capture.\n
\n
While the camera is stopped, the value of StructCameraStatus.CameraCurrentState will be ::c_CameraModeStop.\n
\n
While the camera is capturing, the value of StructCameraStatus.CameraCurrentState will be ::c_CameraModeContinuousCaptureToCameraRAM.\n
\n
\n
In this mode, when the start MS_StartCaptureOrDownload() command is sent, the camera will start a high-speed capture and save the video in the camera's RAM until the MS_StopCaptureOrDownload() command is sent.\n
\n
Once the camera's RAM is full, it is overwritten (looped) until the MS_StopCaptureOrDownload() command is sent.\n
\n
<b>Note:</b> The preview frames sent by the camera during the high-speed capture are only a small sample of the frames that were saved to Camera RAM.  In order to download all of the captured video to the PC, you will need to use \ref downloadtopcmode.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n

@{
*/
/*!
@}
*/

/*! \defgroup triggermode Start/Stop by Trigger Mode

To set the camera to Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM.\n
\n
Use the MS_StartCaptureOrDownload() function to start the capture, and use the MS_StopCaptureOrDownload() function to stop the capture.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.


\n
\n
In this mode, the camera's behavior will be determined by which \ref triggertypenumbers "Trigger Type" the camera is set to.\n
\n
See the documentation of each of the trigger types for more information:\n
\n
\copydoc triggertypevalues

@{
*/

/*! \defgroup singlestartstoptriggermode Single Start/Stop Trigger Mode

To set the camera to Single Start/Stop Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeSingleStartStop.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeSingleStartStop.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, when the start MS_StartCaptureOrDownload() command is sent, the camera will wait for an external TTL trigger input on the camera's "Trigger" BNC jack to begin capturing at high-speed and begin saving the video in the camera's RAM.\n
\n
If the camera's RAM is full, it will start to loop through.\n
\n
In this mode, the camera will start the capture on the rising edge of the first trigger input and stop capturing on the rising edge of the second trigger input.\n
\n
After the stop trigger is received, the capture will end, and the camera will not respond to any more trigger pulses until the capture is restarted.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n

@{
*/
/*!
@}
*/

/*! \defgroup multiplestartstoptriggermode Multiple Start/Stop Trigger Mode

To set the camera to Multiple Start/Stop Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeMultipleStartStop.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeMultipleStartStop.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, when the start MS_StartCaptureOrDownload() command is sent, the camera will wait for an external TTL trigger input on the camera's "Trigger" BNC jack to begin capturing at high-speed and begin saving the video in the camera's RAM.\n
\n
If the camera's RAM is full, it will start to loop through.\n
\n
In this mode, the camera will start on the rising edge of the first trigger input and stop on the rising edge of the next trigger input.\n
\n
After each stop pulse, the camera will return to waiting for another start pulse.\n
\n
The capture will not stop until the MS_StopCaptureOrDownload() command is sent.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n


@{
*/
/*!
@}
*/

/*! \defgroup singlesequencetriggermode Single Sequence Trigger Mode

To set the camera to Single Sequence Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeSingleSequence.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeSingleSequence.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, when the start MS_StartCaptureOrDownload() command is sent, the camera will wait for an external TTL trigger input on the camera's "Trigger" BNC jack to begin capturing at high-speed and begin saving the video in the camera's RAM.\n
\n
When the camera's RAM is full, the camera will stop, and the capture will end.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n


@{
*/
/*!
@}
*/

/*! \defgroup breakboardtriggermode Breakboard Trigger Mode

To set the camera to Breakboard Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeBreakboard.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeBreakboard.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, the trigger line must be held high for 1 second to arm the camera.\n
\n
While the camera is waiting for the trigger line to be held high for 1 second, the value of StructCaptureStatus::CameraIsArmed will be <b>false</b>.
\n
After the trigger line has been held high for 1 second, the value of StructCaptureStatus::CameraIsArmed will be <b>true</b>.
\n
After the camera is armed, when the breakboard is broken, the camera will start capturing.\n
\n
When the camera's RAM is filled, the camera will stop and the capture will end.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n


@{
*/
/*!
@}
*/

/*! \defgroup switchclosuretriggermode Switch Closure Trigger Mode

To set the camera to Switch Closure Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeSwitchClosure.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeSwitchClosure.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, the trigger line must be held low for 1 second to arm the camera.\n
\n
While the camera is waiting for the trigger line to be held low for 1 second, the value of StructCaptureStatus::CameraIsArmed will be <b>false</b>.
\n
After the trigger line has been held low for 1 second, the value of StructCaptureStatus::CameraIsArmed will be <b>true</b>.
\n
After the camera is armed, when the switch is closed, the camera will start capturing.\n
\n
When the camera's RAM is filled, the camera will stop and the capture will end.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n


@{
*/
/*!
@}
*/

/*! \defgroup slavetriggermode Slave Trigger Mode

To set the camera to Slave Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeSlave.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeSlave.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, the camera will remain idle while the trigger line is held low.\n
\n
The camera will start exposing when the trigger line goes high.\n
\n
The camera will stop exposing and go idle again when the trigger goes low.\n
\n
This means that the capture speed and exposure time can be precisely controlled by the trigger input line.\n
\n
If you connect the strobe output from one camera into the trigger input of a different camera running in Slave Trigger Mode, the slave camera will capture at exactly the same speed and exposure time as the master camera, since the strobe output line goes high when a frame is being exposed, and goes low while the camera is waiting to start exposing the next frame.\n
\n
If the camera's RAM is full, it will start to loop through.\n
\n
In this mode, the exposure time is determined by the width of the trigger pulses, and the frame rate is determined by the frequency of the pulses.\n


@{
*/
/*!
@}
*/

/*! \defgroup multispeedtriggermode Multi-Speed Trigger Mode

To set the camera to Multi-Speed Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeMultiSpeed.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeMultiSpeed.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, the camera will capture at a series of up to 8 different speeds and exposure times, as configured in the ::StructMultiSpeedSettings.

Multi-Speed Trigger Mode can work in one of two very different ways:

When using the first way, "By Trigger Pulse" (if StructMultiSpeedSettings::MultiTriggerEnableByFrames is set to <b>false</b>), you will enter a list of up to 8 different speeds and exposure times.\n
\n
After the MS_StartCaptureOrDownload() command is sent, the camera will be idle until it receives the first trigger pulse.\n
\n
When the camera receives the first trigger pulse, it will start capturing at the first speed and exposure time from the list that you entered.\n
\n
Each time the camera receives a trigger pulse, it will switch to the next speed and exposure time from the list.\n
\n
The capture will end when the camera's RAM is completely filled, or when the MS_StopCaptureOrDownload() command is sent.\n
\n
\n
When using the second way, "By Time Elapsed" (if StructMultiSpeedSettings::MultiTriggerEnableByFrames is set to <b>true</b>), you will enter a list of up to 8 different speeds, exposure times, and time values.\n
\n
These time values can be entered either as the amount of time that you want to capture at each speed, or the number of frames that you want to capture at each speed.\n
\n
After the MS_StartCaptureOrDownload() command is sent, the camera will be idle until it receives the first trigger pulse.\n
\n
When the camera receives the first trigger pulse, it will start capturing at the first speed and exposure time from the list you entered.\n
\n
After the time for the current speed has elapsed, the camera will switch to the next speed and exposure time.\n
\n
The capture will end when the camera's RAM is completely filled, or when you press the MS_StopCaptureOrDownload() command is sent.
\n
In this mode, the camera's capture speed and exposure time settings will come from StructMultiSpeedSettings\n


@{
*/
/*!
@}
*/

/*! \defgroup activetriggermode Active Trigger Mode

To set the camera to Active Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeActive.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeActive.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In Active Trigger Mode, the camera will remain idle whenever the trigger line is held low, and will capture continuously whenever the trigger line is held high.\n
\n
If the camera's RAM is full, it will start to loop through.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n


@{
*/
/*!
@}
*/


/*! \defgroup preposttriggermode Pre/Post Trigger Mode

To set the camera to Pre/Post Trigger Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypePrePost.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypePrePost.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In Pre/Post Trigger Mode, the camera will capture continuously until a trigger pulse, then it will capture a specified number of frames before stopping.\n
\n
The number of frames to capture after the trigger can be specified by ::MS_SetPostTriggerFrames() \n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n

@{
*/
/*!
@}
*/



/*! \defgroup singlesequencewithpreviewmode Single Sequence Trigger With Preview Mode

To set the camera to Single Sequence Trigger With Preview Mode, use the MS_SwitchToCaptureModeByTrigger() function, with the TriggerType parameter set to ::c_TriggerTypeSingleSequenceWithPreview.\n
\n
In this mode, the value of StructCameraStatus.CameraMode will be ::c_CameraModeStartStopByTriggerToCameraRAM, and the value of StructCameraStatus.TriggerType will be ::c_TriggerTypeSingleSequenceWithPreview.\n
\n
See \ref triggermodestatusvariables for information about how to check the camera's status, in this mode.\n
\n
Use the MS_CheckIfCameraHasTriggerType() function to check if this trigger type is supported by this camera.\n
\n
\n
This mode works the same as Single Sequence trigger mode, except that the camera will send preview frames while it is waiting for the trigger pulse.\n
\n
No frames will be saved to Camera RAM until the camera receives the trigger pulse.\n
\n
In this mode, an external TTL trigger source is required.\n
\n
In this mode, when the start MS_StartCaptureOrDownload() command is sent, the camera will wait for an external TTL trigger input on the camera's "Trigger" BNC jack to begin capturing at high-speed and begin saving the video in the camera's RAM.  The camera will display preview frames even when no frames are being saved to Camera RAM.\n
\n
When the camera's RAM is full, the camera will stop, and the capture will end.\n
\n
In this mode, the camera's capture speed and exposure time settings will come from StructBasicCaptureSettings\n


@{
*/
/*!
@}
*/


/*!
@}
*/


/*! \defgroup stopmode Stop Mode

In this mode, the camera is idle.

@{
*/
/*!
@}
*/

/*! \defgroup downloadtopcmode Download To PC Mode

Use this mode to download the captured video from Camera RAM to the PC.\n
\n
Use ::StructDownloadSettings to configure the download settings.\n
\n
You can use the MS_CalculateTotalFramesInCameraRAM() function to check how many frames are stored in Camera RAM.  The download start point and end point must be less than this number.\n
\n
You can also use the functions MS_CalculateMinDownloadSpeed() and MS_CalculateMaxDownloadSpeed() to calculate the allowed values for StructDownloadSettings::DownloadSpeed.\n
\n
You can use ::StructDownloadStatus to monitor the status of the download.\n
\n
If you are downloading to an AVI file, use ::StructAVIFileSettings to configure the AVI file's settings.\n
\n
If you are downloading to a series of BMP or JPG files, use ::StructImageFileSettings to configure the file settings.\n
\n
You can use ::StructFileStatus to monitor the status of saving to the file.\n
\n
You can also use ::StructBufferStatus to monitor the data being saved to PC RAM during the download.

@{
*/
/*!
@}
*/

/*! \defgroup downloadpreviewmode Download Preview Mode

Download Preview Mode is the same as \ref downloadtopcmode,
 except that the camera continuously sends out the same frame, at 10 FPS, instead of downloading continuously through Camera RAM.\n
\n
To set the camera to download preview mode, call the MS_StartPreview() function.\n
To return the camera to idle mode, call the MS_StopPreview() function.\n

@{
*/
/*!
@}
*/

/*! \defgroup autodownloadmode Auto-Download Mode

Auto-Download Mode is the same as \ref downloadtopcmode,
 except that the download starts automatically when the capture is finished, and doesn't need to be manually configured, started, or stopped each time.\n
\n
Use ::StructAutoDownloadSettings to configure the auto-download.\n

@{
*/
/*!
@}
*/

/*! \defgroup precapture Pre-Capture

When the camera is in \ref triggermode, it needs to do a brief pre-capture before arming the camera.\n
\n
The pre-capture will start immediately after the MS_StartCaptureOrDownload() function is called, and will take less than 1 second to finish.\n
\n
After the pre-capture is finished, the camera will be armed, waiting for a trigger.\n
\n
The value of StructCaptureStatus::DoingPreCapture will be <b>true</b> while the pre-capture is in progress, and <b>false</b> at any other time.\n

@{
*/
/*!
@}
*/

/*! \defgroup pausedownloadmode Pause Download Mode

This is the mode the camera will be in if you use the MS_PauseDownload() function to pause a download from camera RAM to the PC.\n
\n
Downloads to or from Camera Flash cannot be paused and resumed (in camera models that have internal Flash RAM).\n
\n
To resume the download, use the MS_ResumeDownload() function.\n
\n
You can use ::StructDownloadStatus.DownloadIsPaused to check if the download is paused.\n

@{
*/
/*!
@}
*/

/*! \defgroup clearcamerarammode Clear Camera RAM Mode

This is the mode the camera will be in when you call the MS_ClearCameraRAM() function.\n
\n
In this mode, the camera will clear the contents of camera RAM.\n
\n
When the clear is finished, all of the frames in Camera RAM will be completely black.\n

@{
*/
/*!
@}
*/

/*! \defgroup autoshutdownmode Auto-Shutdown Mode

The camera has a built-in safety feature to automatically stop the camera if its temperature exceeds 80 degrees Celsius.\n
When the camera automatically stops, it will not respond to any commands until the temperature falls below 80 degrees.\n
This auto-shutdown feature will work even if the camera is not connected to the PC.\n

@{
*/
/*!
@}
*/

/*!
@}
*/





/*! \defgroup miscnotes Notes

These are some extra notes that didn't belong in any other section

@{
*/
/*!
*/

/*! \defgroup cameraid CameraID

This is the unique Camera ID value of the camera you want to apply this function to.\n
This must be the same value that was returned by MS_InitializeCameraID() when you initialized this camera.\n

@{
*/
/*!
@}
*/

/*! \defgroup pstatus pStatus

Returns the status code of the operation.  See \ref statuscodes for more information.\n
This parameter is optional.  If it is not passed, then the status will not be returned.\n

@{
*/
/*!
@}
*/

/*! \defgroup resetinvalidparameterstodefaults resetInvalidParametersToDefaults

If this is set to <b>true</b>, then any invalid parameters will be reset to their default values, and the setting update process will continue as normal\n
If this is set to <b>false</b>, then the setting update process will be aborted if any invalid parameters are found\n
In either case, the value of *pStatus will be updated to indicate that the setting was invalid.\n

@{
*/
/*!
@}
*/

/*! \defgroup functionstoswitchcameramodes Functions to Switch Camera Modes

To select which mode you want the camera to be in, use the following functions:\n
\n
MS_SwitchToCaptureModeContinuous()\n
MS_SwitchToCaptureModeByTrigger()\n
MS_SwitchToDownloadToPCMode()\n
MS_ExitDownloadModeAndReturnToPreviousCaptureMode()\n
MS_StartPreview()\n
MS_StopPreview()\n
MS_PauseDownload()\n
MS_ResumeDownload()\n
MS_ClearCameraRAM()\n

@{
*/
/*!
@}
*/

/*! \defgroup previoussettingsfile Previous Settings File
The DLL will automatically save a settings file for each camera that it connects to, so that it can load these settings the next time it connects to the camera.\n
These files are stored in a subfolder named "Settings" in the folder that your application is run from.\n
The settings files will be named according the \ref cameraid value that was used to connect to the camera.\n

@{
*/
/*!
@}
*/

/*! \defgroup timeout Timeout
There is a timeout feature in the library.\n
In \ref continuousmode, the timeout will occur 10 minutes after the capture is started.\n
In \ref triggermode, the timeout will occur 10 minutes after the first image is acquired, and the timeout countdown will be reset if no frames have been acquired for 250 to 500 milliseconds.\n
This time out period can be adjusted in the DLL, using the MS_SetTimeout() function.\n
However, in order for the timeout feature to work properly, the DLL must still be running, the camera ID must still be valid, and the gigabit cable must still be connected to the camera when the timeout occurs.\n

@{
*/
/*!
@}
*/

/*! \defgroup indeo Indeo
The DLL uses the Indeo codec to save compressed AVI files, most versions of Windows will come with the Indeo codec.\n
The Indeo codec is not included as part of the DLL, however it should be available from the normal camera control software package.\n
The DLL will work with version 5.0 or later of the Indeo codec.\n

@{
*/
/*!
@}
*/

/*! \defgroup cameramodevalues Camera Mode Values

The Mega Speed cameras have the following modes:\n
\n
\ref stopmode\n
\ref downloadtopcmode\n
\ref downloadpreviewmode\n
\ref continuousmode\n
\ref triggermode\n
\ref precapture\n
\ref pausedownloadmode\n
\ref clearcamerarammode\n

@{
*/

/*!
@}
*/

/*! \defgroup triggertypevalues Trigger Type Values

\ref triggermode has the following sub-modes:\n
\n
\ref singlestartstoptriggermode\n
\ref multiplestartstoptriggermode\n
\ref singlesequencetriggermode\n
\ref breakboardtriggermode\n
\ref switchclosuretriggermode\n
\ref slavetriggermode\n
\ref multispeedtriggermode\n
\ref activetriggermode\n
\ref preposttriggermode\n
\ref singlesequencewithpreviewmode\n

@{
*/

/*!
@}
*/

/*! \defgroup triggermodestatusvariables Trigger Mode Status Variables

In any sub-mode of \ref triggermode :\n
\n
Use the MS_StartCaptureOrDownload() function to start the capture, and use the MS_StopCaptureOrDownload() function to stop the capture.\n
\n
In \ref breakboardtriggermode or \ref switchclosuretriggermode, the value StructCaptureStatus::CameraIsArmed can be used to check if the camera has been armed yet:\n
\n
In any of the trigger modes, the value StructCaptureStatus::WaitingForTrigger can be used to check if the camera is currently capturing, or waiting for a trigger:\n
\n
Also, the value StructCaptureStatus::DoingPreCapture can be used to check if the camera is still doing its \ref precapture :\n
\n
\n
While the camera is stopped:\n
the value of StructCameraStatus.CameraCurrentState will be ::c_CameraModeStop.\n
\n
While the camera is doing its \ref precapture :\n
the value of StructCameraStatus.CameraCurrentState will be ::c_CameraModeStartStopByTriggerToCameraRAM,\n
and the value of StructCaptureStatus::DoingPreCapture will be <b>true</b>.\n
\n
While the camera is armed, and waiting for a trigger:\n
the value of StructCameraStatus.CameraCurrentState will be ::c_CameraModeStartStopByTriggerToCameraRAM,\n
the value of StructCaptureStatus.WaitingForTrigger will be <b>true</b>,\n
and the value of StructCaptureStatus::DoingPreCapture will be <b>false</b>.\n
\n
While the camera is capturing:\n
the value of StructCameraStatus.CameraCurrentState will be ::c_CameraModeStartStopByTriggerToCameraRAM,\n
the value of StructCaptureStatus.WaitingForTrigger will be <b>false</b>,\n
and the value of StructCaptureStatus::DoingPreCapture will be <b>false</b>.\n

@{
*/

/*!
@}
*/

/*! \defgroup binning Binning

For the camera models that have the Binning feature, this feature will allow the cameras to bin a large, dark image into a smaller, brighter image, in situations where there is very little light available.\n
\n
To check if a camera supports the binning feature, use the MS_CheckIfCameraHasBinning() function.\n
\n
To adjust the binning settings, use ::StructBinningSettings.\n
\n
When binning is enabled, you must set the camera to the size you want the image to be before binning is applied.\n
\n
The images that the camera sends back will be the reduced image size, after binning is applied.\n

\copydoc functionsthatuseimagesizebeforebinning

\copydoc functionsthatuseimagesizeafterbinning

@{
*/

/*!
@}
*/

/*! \defgroup functionsthatuseimagesizebeforebinning Functions that use the Image Size before Binning is applied

The formulas for the capture speed and exposure time are based on the image size before \ref binning.\n
\n
The variables that store the image size before \ref binning are:\n
StructCurrentImageSize::ImageWidthInCameraBeforeBinning and\n
StructCurrentImageSize::ImageHeightInCameraBeforeBinning\n
\n
The functions that use the image width and height before \ref binning are:\n
MS_CalculateMaxCaptureSpeed()\n
MS_CalculateMinImageWidth()\n
MS_CalculateMaxImageWidth()\n
MS_CalculateMinImageHeight()\n
MS_CalculateMaxImageHeight()\n
MS_CalculateImageWidthRoundingValue()\n
MS_CalculateImageHeightRoundingValue()\n
MS_ChangeImageSize()\n
MS_SaveSettingsToPresetFile()\n
MS_LoadSettingsFromPresetFile()\n
\attention This list may be incomplete.

@{
*/

/*!
@}
*/

/*! \defgroup functionsthatuseimagesizeafterbinning Functions that use the Image Size after Binning is applied

The formulas for downloading from the camera are based on the image size after \ref binning.\n
\n
The variables that store the image size after \ref binning are:\n
StructCurrentImageSize::ImageWidthInCameraAfterBinning and\n
StructCurrentImageSize::ImageHeightInCameraAfterBinning\n
\n
The functions that use the image width and height after \ref binning are:\n
MS_CalculateMaxDownloadSpeed()\n
MS_CalculateTotalFramesInCameraRAM()\n
\attention This list may be incomplete.

@{
*/

/*!
@}
*/

/*! \defgroup functionsthatuseimagesizefromcamera Functions that use the Image Size of the frames sent from the Camera

The buffer that the camera uses to send the preview frame to the PC while a capture is in progress has a limited size.\n
If the requested image size is to large to fit in this buffer, then the width and height of the preview images will be cut in half, so that they will fit in the buffer.\n
When the images are downloaded from camera RAM, they will be downloaded at full resolution.\n
Only the preview images sent to the PC while the capture is in progress will be affected by this limited bufer size.\n
Use the function MS_CalculateMaxPreviewImageSize() to calculate the maximum allowed size for the preview images, in pixels.\n
Also, if \ref binning is enabled, then these values will be based on the image size after \ref binning is applied.\n
All of the functions that manipulate the images in PC RAM are based on these values.\n
\n
The variables that store the image size before \ref binning are:\n
StructCurrentImageSize::ImageWidthFromCamera and\n
StructCurrentImageSize::ImageHeightFromCamera\n
\n
The functions that use the Image Size of the frames sent from the Camera are:\n
MS_CalculateMaxPreviewImageSize()\n
MS_DoPostProcessingBW()\n
MS_DoPostProcessingColor()\n
MS_DoPostProcessingGrayscale()\n
MS_SaveToAVI()\n
MS_SaveToImageFile()\n
MS_WriteOneBMPFromBuffer()\n
MS_ReadTimeStampFromFrame()\n
MS_ReadRS422DataFromFrame()\n
MS_GetColorImage()\n
MS_GetGrayscaleImage()\n
MS_ApplyGamma()\n
\attention This list may be incomplete.

@{
*/

/*!
@}
*/

/*! \defgroup rs422 RS-422

For the camera models that have the RS-422 feature, this feature will allow the cameras to save the RS-422 data to the AVI files that you download from the camera, and then extract this data from the AVI file to a text file.\n
\n
To check if a camera supports the RS-422 feature, use the MS_CheckIfCameraHasRS422() function.\n
\n
To adjust the RS422 settings, use the MS_GetRS422DataBytes(), MS_SetRS422DataBytes(), MS_GetRS422IsInverted(), and MS_SetRS422IsInverted() functions.\n
\n
To check if the camera has successfully locked onto the RS422 signal, use the MS_CheckIfRS422IsLocked() function.\n
\n
To download from the camera to an AVI file, set StructDownloadSettings.DestFileType to \ref c_DownloadToAVI , as shown in the function example3() in the DLL test program.\n
\n
To extract the RS422 data from an AVI file to a text file, use the MS_ExtractRS422DataToFile() function.\n

@{
*/

/*!
@}
*/

/*! \defgroup autoexposure Auto-Exposure

For the camera models that have the Auto-Exposure feature, this feature will allow the cameras to automatically adjust the exposure time to set the image to a target brightness level.\n
\n
To check if a camera supports the auto-exposure feature, use the MS_CheckIfCameraHasAutoExposure() function.\n
\n
To adjust the auto-exposure settings, use ::StructAutoExposureSettings.\n
\n
The StructBasicCaptureSettings.ExposureTime will not be used when auto-exposure is enabled.\n

@{
*/

/*!
@}
*/

/*! \defgroup eswitch E-Switch

For the camera models that have the E-Switch feature, this feature will allow the cameras to use the camera's Marker/E-Switch input as either a Marker input or an E-Switch input.  When it is set to a Marker input, the Marker number in the Screen Overlay will increase by 1 every time a marker pulse is received.   When it is set to an E-Switch input, the camera will only respond to trigger pulses on the trigger input line when the E-Switch line is held high.\n
\n
To check if a camera supports the E-Switch feature, use the MS_CheckIfCameraHasESwitch() function.\n
\n
To switch between Marker mode and E-Switch mode, use the MS_UseMarkerAsMarker() and MS_UseMarkerAsESwitch() functions.\n

@{
*/

/*!
@}
*/

/*!
@}
*/

/***************************************************************************************************************************************/


/*! \cond INTERNAL
*/

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//get struct with strings through DLL boundary

struct _Proxy_StructOverlaySettings
{
	bool MarkerSelected           ;
	bool GigabitTimeStampSelected ;
	bool IRIGTimeStampSelected    ;
	bool CaptureStartDateSelected ;
	bool CaptureSpeedSelected     ;
	bool ExposureTimeSelected     ;
	bool Custom1Selected          ;
	bool Custom2Selected          ;
	bool AtoDDataSelected         ;
	bool RS422DataSelected        ;

	const char* CustomDataString1;
	const char* CustomDataString2;

	int OverlayChoiceTopLeft;
	int OverlayChoiceTopRight;
	int OverlayChoiceBottomLeft;
	int OverlayChoiceBottomRight;

	bool EnableOverlay;
};

struct _Proxy_StructAVIFileSettings
{
	int AVIFileQuality;

	const char* AVIAttachedNote;
	const char* AVIFileName;

	int AVIFirstFrame;
	int AVILastFrame;
	bool AVIIsCompressed;
};


struct _Proxy_StructImageFileSettings
{
	int JPGFileQuality;
	bool TIFFileIsCompressed;

	const char* ImageFileName;

	int ImageFileFirstFrame;
	int ImageFileLastFrame;
	int ImageFileType;
};


struct _Proxy_StructAutoDownloadSettings
{
	int AutoDownloadSpeed;
	int AutoDownloadStartFrame;
	int AutoDownloadEndFrame;
	int AutoDownloadFileType;

	const char* AutoDownloadFileName;

	bool AutoDownloadAutoAdjustSpeed;
	bool AutoDownloadAutoAdjustFrames;
	bool AutoDownloadAutoCloseDLManager;
	bool AutoDownloadAutoRearmCamera;
	bool EnableAutoDownloadToPC;
	bool AutoDownloadByPrePostFrames;
	int AutoDownloadPreTriggerFrames;
	int AutoDownloadPostTriggerFrames;
};


struct _Proxy_StructDownloadSettings
{
	int DownloadSpeed;
	int DownloadStartPos;
	int DownloadEndPos;
	bool UseDownloadEndPos;

	const char*DestFileName;

	int DestFileType;
};

struct _Proxy_StructFileStatus
{
	unsigned __int64 CurrentAVIFileSize;

	bool InSaveOverloadProcess;
	bool InSaveToFileProcess;

	const char* AVISAVENewName;
	const char* BMPSAVENewName;
	const char* JPGSAVENewName;

	bool FinishedSavingAVI;
	bool FinishedSavingCompressedAVI;
	bool FinishedSavingBMP;
	bool FinishedSavingJPG;
};

struct _Proxy_StructGigabitConnectionStatus
{
	bool CameraIsConnected;
	bool IsSelectingCamera;
	bool IsConnectingToCamera;

	bool WasConnected;

	const char* LastDeviceMAC;
	const char* LastDeviceIP;
	const char* LastDeviceName;

	int LastConnectedMode;
	char CurrentMacAddress[18];
};

struct _Proxy_StructDataFromAVIFile
{
	long totalFrames                  ; ///<   1 - the number of frames in the AVI file
	long imageWidth                   ; ///<   2 - the image width
	long imageHeight                  ; ///<   3 - the image height
	long captureSpeed                 ; ///<   6 - the capture speed, in FPS
	double fileSize                   ; ///<   8 - the size of the AVI file, in megabytes
	SYSTEMTIME downloadDate           ; ///<   9 - the date the AVI file was downloaded from the camera

	double softwareCodeVersion        ; ///< 118 - software code version
	double cameraCodeVersion          ; ///< 119 - camera code version

	int CameraMode                    ; ///< 121 - camera mode
	int triggerType                   ; ///< 122 - trigger type
	long exposureTime                 ; ///< 123 - exposure time
	long gainValue                    ; ///< 126 - gain value
	long boostLevel                   ; ///< 129 - boost level (70K and 75K only)

	int displayMode                   ; ///< 130 - display mode
	int bayerRed                      ; ///< 131 - bayer red
	int bayerGreen                    ; ///< 132 - bayer green
	int bayerBlue                     ; ///< 133 - bayer blue
	double bayerGamma                 ; ///< 134 - bayer gamma

	int VerticalReticleX              ; ///< 140 - vertical reticle X
	int VerticalReticleColor          ; ///< 141 - vertical reticle color
	int CrosshairReticleX             ; ///< 142 - crosshair reticle X
	int CrosshairReticleY             ; ///< 143 - crosshair reticle Y
	int CrosshairReticleColor         ; ///< 144 - crosshair reticle color
	int CrosshairReticleWidth         ; ///< 145 - crosshair reticle width
	int CrosshairReticleHeight        ; ///< 146 - crosshair reticle height
	int CrosshairReticleWidthType     ; ///< 147 - crosshair reticle width type
	int CrosshairReticleHeightType    ; ///< 148 - crosshair reticle height type

	int bayerWhite                    ; ///< 156 - bayer white (intensity)
	double bayerRawGamma              ; ///< 157 - bayer raw gamma ( for intensity )

	int encodedDataRows               ; ///< 171 - encoded data rows
	int RS422DataBytes                ; ///< 177 - RS422 data bytes

    bool EnableAutoExposure           ; ///< 178 - EnableAutoExposure;

    int AutoExposureTargetValue       ; ///< 179 - AutoExposureTargetValue;
    int AutoExposureErrorMargin       ; ///< 180 - AutoExposureErrorMargin;
    int AutoExposureMinExposureTime   ; ///< 181 - AutoExposureMinExposureTime;
    int AutoExposureMaxExposureTime   ; ///< 182 - AutoExposureMaxExposureTime;

    int AutoExposureWindowWidth       ; ///< 183 - AutoExposureWindowWidth;
    int AutoExposureWindowHeight      ; ///< 184 - AutoExposureWindowHeight;
    int AutoExposureTargetLocationX   ; ///< 185 - AutoExposureTargetLocationX;
    int AutoExposureTargetLocationY   ; ///< 186 - AutoExposureTargetLocationY;

	bool AutoExposureIsHighSensitivity; ///< 187 - AutoExposureIsHighSensitivity;

	const char* cameraType            ; ///< 199 - the camera type
};


MS_CAMERACONTROL_API const _Proxy_StructOverlaySettings	INTERNAL_GetOverlaySettings(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructAVIFileSettings	INTERNAL_GetAVIFileSettings(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructImageFileSettings INTERNAL_GetImageFileSettings(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructAutoDownloadSettings INTERNAL_GetAutoDLSettings(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructDownloadSettings INTERNAL_GetDownloadSettings(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructFileStatus INTERNAL_GetFileStatus(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructGigabitConnectionStatus INTERNAL_GetGigabitConnectionStatus(long CameraID, int* pStatus);
MS_CAMERACONTROL_API const _Proxy_StructDataFromAVIFile INTERNAL_ReadAVIFileData( long CameraID, const char* FileName, int* pStatus );

MS_CAMERACONTROL_API int INTERNAL_SetOverlaySettings(long CameraID, const _Proxy_StructOverlaySettings &ProxyStruct, bool reset, int* pStatus);
MS_CAMERACONTROL_API int INTERNAL_SetAVIFileSettings(long CameraID, const _Proxy_StructAVIFileSettings &ProxyStruct, bool reset, int* pStatus);
MS_CAMERACONTROL_API int INTERNAL_SetImageFileSettings(long CameraID, const _Proxy_StructImageFileSettings ProxyStruct, bool reset, int* pStatus);
MS_CAMERACONTROL_API int INTERNAL_SetAutoDownloadSettings(long CameraID, const _Proxy_StructAutoDownloadSettings &ProxyStruct, bool reset, int* pStatus);
MS_CAMERACONTROL_API int INTERNAL_SetDownloadSettings(long CameraID, const _Proxy_StructDownloadSettings &ProxyStruct, bool reset, int* pStatus);



inline void ToProxy_OverlaySettings(const StructOverlaySettings &App,	_Proxy_StructOverlaySettings &Proxy)
{
	Proxy.MarkerSelected           		= App.MarkerSelected           ;
	Proxy.GigabitTimeStampSelected 		= App.GigabitTimeStampSelected ;
	Proxy.IRIGTimeStampSelected    		= App.IRIGTimeStampSelected    ;
	Proxy.CaptureStartDateSelected 		= App.CaptureStartDateSelected ;
	Proxy.CaptureSpeedSelected     		= App.CaptureSpeedSelected     ;
	Proxy.ExposureTimeSelected     		= App.ExposureTimeSelected     ;
	Proxy.Custom1Selected          		= App.Custom1Selected          ;
	Proxy.Custom2Selected          		= App.Custom2Selected          ;
	Proxy.AtoDDataSelected         		= App.AtoDDataSelected         ;
	Proxy.RS422DataSelected        		= App.RS422DataSelected        ;

	Proxy.CustomDataString1				= App.CustomDataString1.c_str();
	Proxy.CustomDataString2				= App.CustomDataString2.c_str();

	Proxy.OverlayChoiceTopLeft			= App.OverlayChoiceTopLeft		;
	Proxy.OverlayChoiceTopRight			= App.OverlayChoiceTopRight		;
	Proxy.OverlayChoiceBottomLeft		= App.OverlayChoiceBottomLeft	;
	Proxy.OverlayChoiceBottomRight		= App.OverlayChoiceBottomRight	;
	Proxy.EnableOverlay					= App.EnableOverlay				;
}

inline void ToProxy_AVIFileSettings(const StructAVIFileSettings &App, _Proxy_StructAVIFileSettings &Proxy)
{
	Proxy.AVIFileQuality	= App.AVIFileQuality;

	Proxy.AVIAttachedNote	= App.AVIAttachedNote.c_str();
	Proxy.AVIFileName		= App.AVIFileName.c_str();

	Proxy.AVIFirstFrame		= App.AVIFirstFrame;
	Proxy.AVILastFrame		= App.AVILastFrame;
	Proxy.AVIIsCompressed	= App.AVIIsCompressed;
}

inline void ToProxy_ImageFileSettings(const StructImageFileSettings &App, _Proxy_StructImageFileSettings &Proxy)
{
	Proxy.JPGFileQuality		= App.JPGFileQuality;
	Proxy.TIFFileIsCompressed	= App.TIFFileIsCompressed;

	Proxy.ImageFileName			= App.ImageFileName.c_str();

	Proxy.ImageFileFirstFrame	= App.ImageFileFirstFrame;
	Proxy.ImageFileLastFrame	= App.ImageFileLastFrame;
	Proxy.ImageFileType			= App.ImageFileType;
}

inline void ToProxy_AutoDLSettings(const StructAutoDownloadSettings &App, _Proxy_StructAutoDownloadSettings &Proxy)
{
	Proxy.AutoDownloadSpeed				= App.AutoDownloadSpeed;
	Proxy.AutoDownloadStartFrame		= App.AutoDownloadStartFrame;
	Proxy.AutoDownloadEndFrame			= App.AutoDownloadEndFrame;
	Proxy.AutoDownloadFileType			= App.AutoDownloadFileType;

	Proxy.AutoDownloadFileName			= App.AutoDownloadFileName.c_str();

	Proxy.AutoDownloadAutoAdjustSpeed	= App.AutoDownloadAutoAdjustSpeed;
	Proxy.AutoDownloadAutoAdjustFrames	= App.AutoDownloadAutoAdjustFrames;
	Proxy.AutoDownloadAutoCloseDLManager= App.AutoDownloadAutoCloseDLManager;
	Proxy.AutoDownloadAutoRearmCamera	= App.AutoDownloadAutoRearmCamera;
	Proxy.EnableAutoDownloadToPC		= App.EnableAutoDownloadToPC;
	Proxy.AutoDownloadByPrePostFrames	= App.AutoDownloadByPrePostFrames;
	Proxy.AutoDownloadPreTriggerFrames	= App.AutoDownloadPreTriggerFrames;
	Proxy.AutoDownloadPostTriggerFrames	= App.AutoDownloadPostTriggerFrames;
}
inline void ToProxy_DownloadSettings(const StructDownloadSettings &App, _Proxy_StructDownloadSettings &Proxy)
{
	Proxy.DownloadSpeed		= App.DownloadSpeed;
	Proxy.DownloadStartPos	= App.DownloadStartPos;
	Proxy.DownloadEndPos	= App.DownloadEndPos;
	Proxy.UseDownloadEndPos	= App.UseDownloadEndPos;

	Proxy.DestFileName		= App.DestFileName.c_str();

	Proxy.DestFileType		= App.DestFileType;
}


inline void ProxyTo_OverlaySettings(StructOverlaySettings &App, const _Proxy_StructOverlaySettings &Proxy)
{
	App.MarkerSelected           		= Proxy.MarkerSelected           ;
	App.GigabitTimeStampSelected 		= Proxy.GigabitTimeStampSelected ;
	App.IRIGTimeStampSelected    		= Proxy.IRIGTimeStampSelected    ;
	App.CaptureStartDateSelected 		= Proxy.CaptureStartDateSelected ;
	App.CaptureSpeedSelected     		= Proxy.CaptureSpeedSelected     ;
	App.ExposureTimeSelected     		= Proxy.ExposureTimeSelected     ;
	App.Custom1Selected          		= Proxy.Custom1Selected          ;
	App.Custom2Selected          		= Proxy.Custom2Selected          ;
	App.AtoDDataSelected         		= Proxy.AtoDDataSelected         ;
	App.RS422DataSelected        		= Proxy.RS422DataSelected        ;

	App.CustomDataString1				= Proxy.CustomDataString1;
	App.CustomDataString2				= Proxy.CustomDataString2;

	App.OverlayChoiceTopLeft			= Proxy.OverlayChoiceTopLeft		;
	App.OverlayChoiceTopRight			= Proxy.OverlayChoiceTopRight		;
	App.OverlayChoiceBottomLeft			= Proxy.OverlayChoiceBottomLeft		;
	App.OverlayChoiceBottomRight		= Proxy.OverlayChoiceBottomRight	;
	App.EnableOverlay					= Proxy.EnableOverlay				;
}
inline void ProxyTo_AVIFileSettings(StructAVIFileSettings &App, const _Proxy_StructAVIFileSettings &Proxy)
{
	App.AVIFileQuality		= Proxy.AVIFileQuality;

	App.AVIAttachedNote		= Proxy.AVIAttachedNote;
	App.AVIFileName			= Proxy.AVIFileName;

	App.AVIFirstFrame		= Proxy.AVIFirstFrame;
	App.AVILastFrame		= Proxy.AVILastFrame;
	App.AVIIsCompressed		= Proxy.AVIIsCompressed;
}
inline void ProxyTo_ImageFileSettings(StructImageFileSettings &App, const _Proxy_StructImageFileSettings &Proxy)
{
	App.JPGFileQuality			= Proxy.JPGFileQuality;
	App.TIFFileIsCompressed		= Proxy.TIFFileIsCompressed;

	App.ImageFileName			= Proxy.ImageFileName;

	App.ImageFileFirstFrame		= Proxy.ImageFileFirstFrame;
	App.ImageFileLastFrame		= Proxy.ImageFileLastFrame;
	App.ImageFileType			= Proxy.ImageFileType;
}
inline void ProxyTo_AutoDLSettings(StructAutoDownloadSettings &App, const _Proxy_StructAutoDownloadSettings &Proxy)
{
	App.AutoDownloadSpeed				= Proxy.AutoDownloadSpeed;
	App.AutoDownloadStartFrame			= Proxy.AutoDownloadStartFrame;
	App.AutoDownloadEndFrame			= Proxy.AutoDownloadEndFrame;
	App.AutoDownloadFileType			= Proxy.AutoDownloadFileType;

	App.AutoDownloadFileName			= Proxy.AutoDownloadFileName;

	App.AutoDownloadAutoAdjustSpeed		= Proxy.AutoDownloadAutoAdjustSpeed;
	App.AutoDownloadAutoAdjustFrames	= Proxy.AutoDownloadAutoAdjustFrames;
	App.AutoDownloadAutoCloseDLManager	= Proxy.AutoDownloadAutoCloseDLManager;
	App.AutoDownloadAutoRearmCamera		= Proxy.AutoDownloadAutoRearmCamera;
	App.EnableAutoDownloadToPC			= Proxy.EnableAutoDownloadToPC;
	App.AutoDownloadByPrePostFrames		= Proxy.AutoDownloadByPrePostFrames;
	App.AutoDownloadPreTriggerFrames	= Proxy.AutoDownloadPreTriggerFrames;
	App.AutoDownloadPostTriggerFrames	= Proxy.AutoDownloadPostTriggerFrames;
}
inline void ProxyTo_DownloadSettings(StructDownloadSettings &App, const _Proxy_StructDownloadSettings &Proxy)
{
	App.DownloadSpeed		= Proxy.DownloadSpeed;
	App.DownloadStartPos	= Proxy.DownloadStartPos;
	App.DownloadEndPos		= Proxy.DownloadEndPos;
	App.UseDownloadEndPos	= Proxy.UseDownloadEndPos;

	App.DestFileName		= Proxy.DestFileName;

	App.DestFileType		= Proxy.DestFileType;
}

inline void ProxyTo_FileStatus(StructFileStatus &App, const _Proxy_StructFileStatus &Proxy)
{
	App.CurrentAVIFileSize			= Proxy.CurrentAVIFileSize;
	App.InSaveOverloadProcess		= Proxy.InSaveOverloadProcess;
	App.InSaveToFileProcess			= Proxy.InSaveToFileProcess;

	App.AVISAVENewName				= Proxy.AVISAVENewName;
	App.BMPSAVENewName				= Proxy.BMPSAVENewName;
	App.JPGSAVENewName				= Proxy.JPGSAVENewName;

	App.FinishedSavingAVI			= Proxy.FinishedSavingAVI;
	App.FinishedSavingCompressedAVI	= Proxy.FinishedSavingCompressedAVI;
	App.FinishedSavingBMP			= Proxy.FinishedSavingBMP;
	App.FinishedSavingJPG			= Proxy.FinishedSavingJPG;
}

inline void ProxyTo_GigabitConnectionStatus(StructGigabitConnectionStatus &App, const _Proxy_StructGigabitConnectionStatus &Proxy)
{
	App.CameraIsConnected			= Proxy.CameraIsConnected;
	App.IsSelectingCamera			= Proxy.IsSelectingCamera;
	App.IsConnectingToCamera		= Proxy.IsConnectingToCamera;
	App.WasConnected				= Proxy.WasConnected;	

	App.LastDeviceMAC	= Proxy.LastDeviceMAC;
	App.LastDeviceIP	= Proxy.LastDeviceIP;
	App.LastDeviceName	= Proxy.LastDeviceName;

	memcpy(&App.LastConnectedMode, &Proxy.LastConnectedMode, sizeof(App.LastConnectedMode));
	memcpy(&App.CurrentMacAddress, &Proxy.CurrentMacAddress, sizeof(App.CurrentMacAddress));
}

inline void ProxyTo_DataFromAVIFile(StructDataFromAVIFile &App, const _Proxy_StructDataFromAVIFile &Proxy)
{
	App.totalFrames						= Proxy.totalFrames;				
	App.imageWidth						= Proxy.imageWidth;
	App.imageHeight						= Proxy.imageHeight;
	App.captureSpeed					= Proxy.captureSpeed;
	App.fileSize						= Proxy.fileSize;
	App.downloadDate					= Proxy.downloadDate;

	App.softwareCodeVersion				= Proxy.softwareCodeVersion;
	App.cameraCodeVersion				= Proxy.cameraCodeVersion;

	App.CameraMode						= Proxy.CameraMode;
	App.triggerType						= Proxy.triggerType;
	App.exposureTime					= Proxy.exposureTime;
	App.gainValue						= Proxy.gainValue;
	App.boostLevel						= Proxy.boostLevel;

	App.displayMode						= Proxy.displayMode;
	App.bayerRed						= Proxy.bayerRed;
	App.bayerGreen						= Proxy.bayerGreen;
	App.bayerBlue						= Proxy.bayerBlue;
	App.bayerGamma						= Proxy. bayerGamma;

	App.VerticalReticleX				= Proxy.VerticalReticleX;
	App.VerticalReticleColor			= Proxy.VerticalReticleColor;
	App.CrosshairReticleX				= Proxy.CrosshairReticleX;
	App.CrosshairReticleY				= Proxy.CrosshairReticleY;
	App.CrosshairReticleColor			= Proxy.CrosshairReticleColor;
	App.CrosshairReticleWidth			= Proxy.CrosshairReticleWidth;
	App.CrosshairReticleHeight			= Proxy.CrosshairReticleHeight;
	App.CrosshairReticleWidthType		= Proxy.CrosshairReticleWidthType;
	App.CrosshairReticleHeightType		= Proxy.CrosshairReticleHeightType;

	App.bayerWhite						= Proxy.bayerWhite;
	App.bayerRawGamma					= Proxy.bayerRawGamma;

	App.encodedDataRows					= Proxy.encodedDataRows;
	App.RS422DataBytes					= Proxy.RS422DataBytes;

	App.EnableAutoExposure				= Proxy.EnableAutoExposure;

	App.AutoExposureTargetValue			= Proxy.AutoExposureTargetValue;
	App.AutoExposureErrorMargin			= Proxy.AutoExposureErrorMargin;
	App.AutoExposureMinExposureTime		= Proxy.AutoExposureMinExposureTime;
	App.AutoExposureMaxExposureTime		= Proxy.AutoExposureMaxExposureTime;

	App.AutoExposureWindowWidth			= Proxy.AutoExposureWindowWidth;
	App.AutoExposureWindowHeight		= Proxy.AutoExposureWindowHeight;
	App.AutoExposureTargetLocationX		= Proxy.AutoExposureTargetLocationX;
	App.AutoExposureTargetLocationY		= Proxy.AutoExposureTargetLocationY;
	App.AutoExposureIsHighSensitivity	= Proxy.AutoExposureIsHighSensitivity;

	App.cameraType						= Proxy.cameraType;
}




inline const StructOverlaySettings MS_GetOverlaySettings(long CameraID, int* pStatus)
{
	_Proxy_StructOverlaySettings ProxyStruct = INTERNAL_GetOverlaySettings(CameraID, pStatus);
	StructOverlaySettings Output;
	ProxyTo_OverlaySettings(Output, ProxyStruct);
	return Output;
}
inline const StructAVIFileSettings MS_GetAVIFileSettings(long CameraID, int* pStatus)
{
	_Proxy_StructAVIFileSettings ProxyStruct = INTERNAL_GetAVIFileSettings(CameraID, pStatus);
	StructAVIFileSettings Output;
	ProxyTo_AVIFileSettings(Output, ProxyStruct);
	return Output;
}
inline const StructImageFileSettings MS_GetImageFileSettings(long CameraID, int* pStatus)
{
	_Proxy_StructImageFileSettings ProxyStruct = INTERNAL_GetImageFileSettings(CameraID, pStatus);
	StructImageFileSettings Output;
	ProxyTo_ImageFileSettings(Output, ProxyStruct);
	return Output;
}
inline const StructAutoDownloadSettings MS_GetAutoDownloadSettings(long CameraID, int* pStatus)
{
	_Proxy_StructAutoDownloadSettings ProxyStruct = INTERNAL_GetAutoDLSettings(CameraID, pStatus);
	StructAutoDownloadSettings Output;
	ProxyTo_AutoDLSettings(Output, ProxyStruct);
	return Output;
}
inline const StructDownloadSettings MS_GetDownloadSettings(long CameraID, int* pStatus)
{
	_Proxy_StructDownloadSettings ProxyStruct = INTERNAL_GetDownloadSettings(CameraID, pStatus);
	StructDownloadSettings Output;
	ProxyTo_DownloadSettings(Output, ProxyStruct);
	return Output;
}

inline const StructFileStatus MS_GetFileStatus(long CameraID, int* pStatus)
{
	_Proxy_StructFileStatus ProxyStruct = INTERNAL_GetFileStatus(CameraID, pStatus);
	StructFileStatus Output;
	ProxyTo_FileStatus(Output, ProxyStruct);
	return Output;
}

inline const StructGigabitConnectionStatus MS_GetGigabitConnectionStatus(long CameraID, int* pStatus)
{
	_Proxy_StructGigabitConnectionStatus ProxyStruct = INTERNAL_GetGigabitConnectionStatus(CameraID, pStatus);
	StructGigabitConnectionStatus Output;
	ProxyTo_GigabitConnectionStatus(Output, ProxyStruct);
	return Output;
}

inline StructDataFromAVIFile MS_ReadAVIFileData(long CameraID, const char* FileName, int* pStatus)
{
	_Proxy_StructDataFromAVIFile ProxyStruct = INTERNAL_ReadAVIFileData(CameraID, FileName, pStatus);
	StructDataFromAVIFile Output;
	ProxyTo_DataFromAVIFile(Output, ProxyStruct);
	return Output;
}


inline int MS_SetOverlaySettings(long CameraID, const StructOverlaySettings &OverlaySettings, bool reset, int* pStatus) 
{
	_Proxy_StructOverlaySettings ProxyStruct;
	ToProxy_OverlaySettings(OverlaySettings, ProxyStruct);
	return INTERNAL_SetOverlaySettings(CameraID, ProxyStruct, reset, pStatus);
}

inline int MS_SetAVIFileSettings(long CameraID, const StructAVIFileSettings &AVIFileSettings, bool reset, int* pStatus) 
{
	_Proxy_StructAVIFileSettings ProxyStruct;
	ToProxy_AVIFileSettings(AVIFileSettings, ProxyStruct);
	return INTERNAL_SetAVIFileSettings(CameraID, ProxyStruct, reset, pStatus) ;
}

inline int MS_SetImageFileSettings(long CameraID, const StructImageFileSettings &ImageFileSettings, bool reset, int* pStatus) 
{
	_Proxy_StructImageFileSettings ProxyStruct;
	ToProxy_ImageFileSettings(ImageFileSettings, ProxyStruct);
	return INTERNAL_SetImageFileSettings(CameraID, ProxyStruct, reset, pStatus) ;
}

inline int MS_SetAutoDownloadSettings(long CameraID, const StructAutoDownloadSettings &AutoDownloadSettings, bool reset, int* pStatus) 
{
	_Proxy_StructAutoDownloadSettings ProxyStruct;
	ToProxy_AutoDLSettings(AutoDownloadSettings, ProxyStruct);
	return INTERNAL_SetAutoDownloadSettings(CameraID, ProxyStruct, reset, pStatus) ;
}

inline int MS_SetDownloadSettings(long CameraID, const StructDownloadSettings &DownloadSettings, bool reset, int* pStatus) 
{
	_Proxy_StructDownloadSettings ProxyStruct;
	ToProxy_DownloadSettings(DownloadSettings, ProxyStruct);
	return INTERNAL_SetDownloadSettings(CameraID, ProxyStruct, reset, pStatus) ;
}


/*! \endcond
*/

#endif // !defined(AFX_MSCAMERACONTROL_H_INCLUDED_)

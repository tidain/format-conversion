package com.gsgc.converter.util

import com.sun.jna.Pointer
import com.sun.jna.WString
import com.sun.jna.platform.win32.Guid
import com.sun.jna.platform.win32.Ole32
import com.sun.jna.platform.win32.WinNT
import com.sun.jna.platform.win32.WTypes
import com.sun.jna.platform.win32.COM.Unknown
import com.sun.jna.ptr.PointerByReference

/**
 * 现代 Windows 资源管理器样式文件/文件夹选择对话框。
 * 基于 COM IFileDialog 接口（Windows Vista+ 原生对话框，带面包屑地址栏、快速访问）。
 */
object WindowsFileDialog {

    private val CLSID_FileOpenDialog = Guid.GUID("DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7")
    private val IID_IFileOpenDialog = Guid.IID("D57C7288-D4AD-4768-BE02-9D969532D960")

    // FILEOPENDIALOGOPTIONS flags
    private const val FOS_PICKFOLDERS = 0x00000020
    private const val FOS_FILEMUSTEXIST = 0x00001000
    private const val FOS_PATHMUSTEXIST = 0x00000800

    // SIGDN flags
    private const val SIGDN_FILESYSPATH = 0x80058000.toInt()

    private val CLSCTX_ALL = WTypes.CLSCTX_INPROC_SERVER or
            WTypes.CLSCTX_INPROC_HANDLER or
            WTypes.CLSCTX_LOCAL_SERVER

    private const val S_OK = 0
    private val RPC_E_CHANGED_MODE = 0x80010106.toInt()

    /**
     * 包装 IFileOpenDialog COM 对象，通过 vtable 索引调用方法。
     * vtable: IUnknown(0-2) -> IModalWindow.Show(3) -> IFileDialog(4-26)
     * 所有方法用 _invokeNativeInt 直接返回 HRESULT(int)，避免 HRESULT 对象构造问题。
     */
    private class FileOpenDialog(ptr: Pointer) : Unknown(ptr) {
        /** Show(HWND) -> HRESULT. args[0] 必须是 this 指针 */
        fun Show(): Int = _invokeNativeInt(3, arrayOf(getPointer(), Pointer.NULL))

        /** SetOptions(FOS) -> HRESULT */
        fun SetOptions(fos: Int): Int = _invokeNativeInt(9, arrayOf(getPointer(), fos))

        /** SetTitle(LPCWSTR) -> HRESULT */
        fun SetTitle(pszTitle: String): Int =
            _invokeNativeInt(17, arrayOf(getPointer(), WString(pszTitle)))

        /** GetResult(IShellItem**) -> HRESULT */
        fun GetResult(ppsi: PointerByReference): Int =
            _invokeNativeInt(20, arrayOf(getPointer(), ppsi))
    }

    /** IShellItem: IUnknown(0-2) -> BindToHandler(3) -> GetParent(4) -> GetDisplayName(5) */
    private class ShellItem(ptr: Pointer) : Unknown(ptr) {
        /** GetDisplayName(SIGDN, LPWSTR*) -> HRESULT */
        fun GetDisplayName(sigdnName: Int, ppszName: PointerByReference): Int =
            _invokeNativeInt(5, arrayOf(getPointer(), sigdnName, ppszName))
    }

    private fun createDialog(): FileOpenDialog? {
        val pbr = PointerByReference()
        val hr = Ole32.INSTANCE.CoCreateInstance(
            CLSID_FileOpenDialog, null, CLSCTX_ALL, IID_IFileOpenDialog, pbr
        )
        if (hr != WinNT.S_OK || pbr.value == null) return null
        return FileOpenDialog(pbr.value)
    }

    /**
     * 显示现代 Windows 打开文件对话框。
     * IFileDialog 必须在 STA 线程中运行，因此在专用线程上执行。
     * @param title 对话框标题
     * @param pickFolders true=选择文件夹，false=选择文件
     * @return 选中的路径，取消则返回 null
     */
    fun showOpenDialog(title: String, pickFolders: Boolean): String? {
        val result = arrayOfNulls<String>(1)
        val latch = java.util.concurrent.CountDownLatch(1)

        val thread = Thread {
            try {
                // 在新线程上初始化 COM 为 STA 模式
                val hrInit = Ole32.INSTANCE.CoInitializeEx(Pointer.NULL, 0x2) // COINIT_APARTMENTTHREADED
                if (hrInit != WinNT.S_OK && hrInit != WinNT.HRESULT(RPC_E_CHANGED_MODE)) {
                    result[0] = null
                    return@Thread
                }
                result[0] = showDialogInternal(title, pickFolders)
            } catch (e: Throwable) {
                e.printStackTrace()
                result[0] = null
            } finally {
                Ole32.INSTANCE.CoUninitialize()
                latch.countDown()
            }
        }
        thread.name = "FileDialog-STA"
        thread.start()
        latch.await()
        return result[0]
    }

    private fun showDialogInternal(title: String, pickFolders: Boolean): String? {
        var dialog: FileOpenDialog? = null
        try {
            dialog = createDialog() ?: return null

            var options = FOS_PATHMUSTEXIST
            if (pickFolders) {
                options = options or FOS_PICKFOLDERS
            } else {
                options = options or FOS_FILEMUSTEXIST
            }
            if (dialog.SetOptions(options) != S_OK) return null
            if (dialog.SetTitle(title) != S_OK) return null

            val hr = dialog.Show()
            if (hr != S_OK) return null // S_FALSE/ERROR_CANCELLED = 用户取消

            val ppsi = PointerByReference()
            if (dialog.GetResult(ppsi) != S_OK) return null

            val shellItem = ShellItem(ppsi.value)
            try {
                val ppszName = PointerByReference()
                if (shellItem.GetDisplayName(SIGDN_FILESYSPATH, ppszName) != S_OK) return null
                val pathPtr = ppszName.value ?: return null
                val path = pathPtr.getWideString(0)
                Ole32.INSTANCE.CoTaskMemFree(pathPtr)
                return path
            } finally {
                shellItem.Release()
            }
        } catch (e: Throwable) {
            e.printStackTrace()
            return null
        } finally {
            dialog?.Release()
        }
    }
}

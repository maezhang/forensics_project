<?php
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_FILES['file'])) {
	$file = $_FILES['file'];
	$upload_dir = 'uploads/';
	$upload_file = $upload_dir . basename($file['name']);
	if (move_uploaded_file($file['tmp_name'], $upload_file)) {
		echo 'File uploaded successfully.';
	} else {
		echo 'Error uploading file.';
	}
}
?>

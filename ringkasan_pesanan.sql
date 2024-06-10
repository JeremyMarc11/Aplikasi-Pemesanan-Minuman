-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 10, 2024 at 12:00 PM
-- Server version: 10.4.27-MariaDB
-- PHP Version: 8.2.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pemesanan_minuman`
--

-- --------------------------------------------------------

--
-- Table structure for table `ringkasan_pesanan`
--

CREATE TABLE `ringkasan_pesanan` (
  `id` int(11) NOT NULL,
  `nama_minuman` varchar(45) NOT NULL,
  `pilihan_rasa` varchar(100) DEFAULT NULL,
  `persentase` varchar(45) DEFAULT NULL,
  `jumlah` int(11) NOT NULL,
  `harga_satuan` int(11) NOT NULL,
  `total_harga` int(11) NOT NULL,
  `status_pembayaran` varchar(45) NOT NULL,
  `status_pesanan` varchar(45) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- Dumping data for table `ringkasan_pesanan`
--

INSERT INTO `ringkasan_pesanan` (`id`, `nama_minuman`, `pilihan_rasa`, `persentase`, `jumlah`, `harga_satuan`, `total_harga`, `status_pembayaran`, `status_pesanan`) VALUES
(1, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(2, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(3, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(4, 'Sirup Dua Rasa', '', '', 2, 15000, 30000, '1', 'Completed'),
(5, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(6, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(7, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(8, 'Sirup Mangga', '', '', 1, 10000, 10000, '1', 'Completed'),
(9, 'Sirup Jeruk', '', '', 2, 10000, 20000, '1', 'Completed'),
(10, 'Sirup Jeruk', '', '', 2, 10000, 20000, '1', 'Completed'),
(11, 'Sirup Coco Pandan', '', '', 3, 10000, 30000, '1', 'Completed'),
(12, 'Sirup Coco Pandan', '', '', 3, 10000, 30000, '1', 'Completed'),
(13, 'Sirup Mangga', '', '', 3, 10000, 30000, '1', 'Completed'),
(14, 'Sirup Mangga', '', '', 2, 10000, 20000, '1', 'Completed'),
(15, 'Sirup Jeruk', '', '', 2, 10000, 20000, '1', 'Completed'),
(16, 'Sirup Mangga', '', '', 2, 10000, 20000, '1', 'Completed'),
(17, 'Sirup Mangga', '', '', 3, 10000, 30000, '1', 'Completed'),
(18, 'Sirup Mangga', '', '', 3, 10000, 30000, '1', 'Completed'),
(19, 'Sirup Mangga', '', '', 3, 10000, 30000, '1', 'Completed'),
(20, 'Sirup Mangga', '', '', 3, 10000, 30000, '1', 'Completed'),
(21, 'Sirup Mangga', '', '', 3, 10000, 30000, '1', 'Completed'),
(22, 'Sirup Melon', '', '', 3, 10000, 30000, '1', 'Completed'),
(23, 'Sirup Coco Pandan', '', '', 3, 10000, 30000, '1', 'Completed'),
(24, 'Sirup Jeruk', NULL, NULL, 2, 10000, 20000, '1', 'Completed'),
(25, 'Sirup Jeruk', NULL, NULL, 3, 10000, 30000, '1', 'Completed'),
(26, 'Sirup Jeruk', NULL, NULL, 2, 10000, 20000, '1', 'Completed'),
(27, 'Sirup Jeruk', NULL, NULL, 3, 10000, 30000, '1', 'Completed'),
(28, 'Sirup Jeruk', NULL, NULL, 2, 10000, 20000, '1', 'Completed'),
(29, 'Sirup Jeruk', NULL, '', 2, 10000, 20000, '1', 'Completed'),
(30, 'Sirup Jeruk', '', '0', 1, 10000, 10000, '1', 'Completed'),
(31, 'Sirup Dua Rasa', '', '0', 1, 15000, 15000, '1', 'Completed'),
(32, 'Sirup Dua Rasa', '', '0', 1, 15000, 15000, '1', 'Completed'),
(33, 'Sirup Dua Rasa', 'Sirup Coco Pandan + Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(34, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(35, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(36, 'Sirup Jeruk', '', '', 7, 10000, 70000, '1', 'Completed'),
(37, 'Sirup Dua Rasa', 'Sirup Coco Pandan + Sirup Jeruk, Sirup Coco Pandan + Sirup Jeruk', '50% - 50%, 25% - 75%', 2, 15000, 30000, '1', 'Completed'),
(38, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(39, 'Sirup Dua Rasa', 'Sirup Jeruk + Sirup Mangga', '25% - 75%', 1, 15000, 15000, '1', 'Completed'),
(40, 'Sirup Coco Pandan', '', '', 1, 10000, 10000, '1', 'Completed'),
(41, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(42, 'Sirup Dua Rasa', '', '', 2, 15000, 30000, '1', 'Completed'),
(43, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(44, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(45, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(46, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(47, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(48, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(49, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(50, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(51, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(52, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(53, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(54, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(55, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(56, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(57, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(58, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(59, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(60, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(61, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(62, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(63, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(64, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(65, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(66, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(67, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(68, 'Sirup Dua Rasa', '', '', 2, 15000, 30000, '1', 'Completed'),
(69, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(70, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(71, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(72, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(73, 'Sirup Dua Rasa', '', '', 1, 15000, 15000, '1', 'Completed'),
(74, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(75, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '25% - 75%', 1, 15000, 15000, '1', 'Completed'),
(76, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(77, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(78, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(79, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(80, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(81, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(82, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(83, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(84, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(85, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(86, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(87, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(88, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(89, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(90, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(91, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(92, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(93, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(94, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(95, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(96, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '', 1, 15000, 15000, '1', 'Completed'),
(97, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(98, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(99, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(100, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(101, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(102, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(103, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(104, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(105, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(106, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(107, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(108, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(109, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(110, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(111, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(112, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(113, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(114, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(115, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(116, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(117, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(118, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(119, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(120, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(121, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(122, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(123, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(124, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(125, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(126, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(127, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(128, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(129, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(130, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(131, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(132, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(133, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(134, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(135, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(136, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(137, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(138, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(139, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '5, 0, %,  , -,  , 5, 0, %', 1, 15000, 15000, '1', 'Completed'),
(140, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(141, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(142, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(143, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(144, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(145, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(146, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(147, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(148, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(149, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(150, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(151, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(152, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(153, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(154, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(155, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(156, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(157, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(158, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(159, 'Sirup Jeruk', '', '', 1, 10000, 10000, '1', 'Completed'),
(160, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Jeruk', '50% - 50%', 1, 15000, 15000, '1', 'Completed'),
(161, 'Sirup Dua Rasa', 'Sirup Coco Pandan, Sirup Mangga', '50% - 50%', 3, 15000, 45000, '1', 'Completed');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ringkasan_pesanan`
--
ALTER TABLE `ringkasan_pesanan`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ringkasan_pesanan`
--
ALTER TABLE `ringkasan_pesanan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=162;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

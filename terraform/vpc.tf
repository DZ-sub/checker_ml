# vpc
resource "aws_vpc" "vpc" {
    # VPC must be large enough to contain the /20 subnets below
    cidr_block           = "10.0.0.0/16"
    enable_dns_support   = true
    enable_dns_hostnames = true

    tags = {
        Name = "${var.project_name}-vpc"
    }
}
# subnet
resource "aws_subnet" "public_subnet_1" {
    vpc_id                  = aws_vpc.vpc.id
    cidr_block              = "10.0.0.0/20"
    availability_zone       = "ap-northeast-1a"
    tags = {
        Name = "${var.project_name}-public-subnet-1"
    }
}
# resource "aws_subnet" "private_subnet_1" {
#     vpc_id                  = aws_vpc.vpc.id
#     cidr_block              = "10.0.16.0/20"
#     availability_zone       = "ap-northeast-1a"
#     tags = {
#         Name = "${var.project_name}-private-subnet-1"
#     }
# }
resource "aws_subnet" "public_subnet_2" {
    vpc_id                  = aws_vpc.vpc.id
    cidr_block              = "10.0.32.0/20"
    availability_zone       = "ap-northeast-1c"
    tags = {
        Name = "${var.project_name}-public-subnet-2"
    }
}
# resource "aws_subnet" "private_subnet_2" {
#     vpc_id                  = aws_vpc.vpc.id
#     cidr_block              = "10.0.48.0/20"
#     availability_zone       = "ap-northeast-1c"
#     tags = {
#         Name = "${var.project_name}-private-subnet-2"
#     }
# }
# route table
resource "aws_route_table" "public_rt" {
    vpc_id = aws_vpc.vpc.id
    tags = {
        Name = "${var.project_name}-public-rt"
    }
}
# resource "aws_route_table" "private_rt_1" {
#     vpc_id = aws_vpc.vpc.id
#     tags = {
#         Name = "${var.project_name}-private-rt-1"
#     }
# }
# resource "aws_route_table" "private_rt_2" {
#     vpc_id = aws_vpc.vpc.id
#     tags = {
#         Name = "${var.project_name}-private-rt-2"
#     }
# }

# ルートテーブル をサブネットに関連付ける
resource "aws_route_table_association" "public_subnet_association" {
    count = length([aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id])
    route_table_id = aws_route_table.public_rt.id
    subnet_id      = element([
        aws_subnet.public_subnet_1.id,
        aws_subnet.public_subnet_2.id,
    ], count.index)
}
# resource "aws_route_table_association" "private_subnet_1_association" {
#     subnet_id      = aws_subnet.private_subnet_1.id
#     route_table_id = aws_route_table.private_rt_1.id
# }
# resource "aws_route_table_association" "private_subnet_2_association" {
#     subnet_id      = aws_subnet.private_subnet_2.id
#     route_table_id = aws_route_table.private_rt_2.id
# }
# internet gateway
resource "aws_internet_gateway" "igw" {
    vpc_id = aws_vpc.vpc.id
    tags = {
        Name = "${var.project_name}-igw"
    }
}
# publicに ngw を配置するための Elastic IP
# resource "aws_eip" "nat_eip_1" {
#     domain = "vpc"
#     tags = {
#         Name = "${var.project_name}-eip-1"
#     }
# }
# resource "aws_eip" "nat_eip_2" {
#     domain = "vpc"
#     tags = {
#         Name = "${var.project_name}-eip-2"
#     }
# }
# nat gateway
# resource "aws_nat_gateway" "ngw_1" {
#     allocation_id = aws_eip.nat_eip_1.id
#     subnet_id     = aws_subnet.public_subnet_1.id
#     tags = {
#         Name = "${var.project_name}-ngw-1"
#     }
#     depends_on = [aws_internet_gateway.igw]
# }
# resource "aws_nat_gateway" "ngw_2" {
#     allocation_id = aws_eip.nat_eip_2.id
#     subnet_id     = aws_subnet.public_subnet_2.id
#     tags = {
#         Name = "${var.project_name}-ngw-2"
#     }
#     depends_on = [aws_internet_gateway.igw]
# }
# igw のアタッチ
resource "aws_route" "public_route" {
    route_table_id         = aws_route_table.public_rt.id
    destination_cidr_block = "0.0.0.0/0"
    gateway_id             = aws_internet_gateway.igw.id
}
# ngw のアタッチ
# resource "aws_route" "private_route_1" {
#     route_table_id         = aws_route_table.private_rt_1.id
#     destination_cidr_block = "0.0.0.0/0"
#     nat_gateway_id         = aws_nat_gateway.ngw_1.id
# }
# resource "aws_route" "private_route_2" {
#     route_table_id         = aws_route_table.private_rt_2.id
#     destination_cidr_block = "0.0.0.0/0"
#     nat_gateway_id         = aws_nat_gateway.ngw_2.id
# }
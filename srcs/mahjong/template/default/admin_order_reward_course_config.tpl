<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/common.js"></script>
      <div class="block">
                %include admin_frame_header
                <div class="content">
                    <table id="dataTable" class="table table-bordered table-hover"></table>
                </div>
</div>
<script type="text/javascript">

    $('#dataTable').bootstrapTable({
          method: 'get',
          url: '{{info["listUrl"]}}',
          contentType: "application/json",
          datatype: "json",
          cache: false,
          striped: true,
          search:true,
          toolbar:'#toolbar',
          pagination: true,
          pageSize: 15,
          pageList: [15, 50, 100],
          columns: [
          [{
              field: 'id',
              title: '奖品套餐id',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'title',
              title: '名称',
              align: 'center',
              valign: 'middle'
          },{
              field: 'cost',
              title: '成本',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'price',
              title: '价格',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'limit_price',
              title: '限买下限值',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'item_id',
              title: '道具id',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'item_type',
              title: '道具类型名称',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'cost_type',
              title: '消耗类型',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'cost_num',
              title: '消耗数量',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'cost_type_name',
              title: '消耗类型名称',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'is_honor',
              title: '是否为荣誉商城套餐',
              align: 'center',
              valign: 'middle',
              sortable: true,
              formatter:is_honor_show
          },{
              field: 'icon',
              title: 'icon',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'op',
              title: '操作',
              align: 'center',
              valign: 'middle',
              formatter:getOp
          }]]
    });

      function del() {
        var msg = "您真的确定要删除吗？\n\n请确认！";
        if (confirm(msg)==true){
            return true;
         }else{
            return false;
        }
      }

       function is_honor_show(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var statusstr = '';
          console.log('-------------------------------')
          console.log('-------------------------------')
          console.log(rowobj['is_honor'])
          console.log('-------------------------------')
          console.log('-------------------------------')
          if(rowobj['is_honor'] == 0){
              statusstr = '<span class="label label-danger">不是</span>';
          }else if(rowobj['is_honor'] == 1){
              statusstr = '<span class="label label-success">是</span>';
          }
          return [
              statusstr
          ].join('');
      }

      function getOp(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          res = "<a onclick='javascript:return del();' href='/admin/order/reward/del?id="+rowobj['id']+"' class='btn btn-primary'>删除</a><a href='/admin/order/reward/modify?id="+rowobj['id']+"' class='btn btn-primary'>修改</a>"
          if(rowobj['is_honor']==0){
            res += "<a href='/admin/order/reward/ishonor?is_honor=1&id="+rowobj['id']+"' class='btn btn-primary'>设置为荣誉商城套餐</a>"
          }else{
            res += "<a href='/admin/order/reward/ishonor?is_honor=0&id="+rowobj['id']+"' class='btn btn-primary'>设置为非荣誉商城套餐</a>"
          }
          return [
            res
          ].join('');
      }

</script>
%rebase admin_frame_base
<script>
    if("{{op_res}}"=="1"){
        alert("修改成功！")
    }else if("{{op_res}}"=="2"){
        alert("修改失败！")
    }else if("{{op_res}}"=="3"){
        alert("删除成功！")
    }else if("{{op_res}}"=="4"){
        alert("删除失败！")
    }
</script>
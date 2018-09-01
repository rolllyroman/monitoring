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
              field: 'ip',
              title: 'IP',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'rkey',
              title: '激活码',
              align: 'center',
              valign: 'middle'
          },{
              field: 'last_req_time',
              title: '最近一次请求时间',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'last_req_rkey',
              title: '最近一次发送激活码',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'rtype',
              title: '最近一次请求类型',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'last_req_code',
              title: '最近一次请求结果',
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
          res = "<a  href='/monitor/set/valid?is_valid=1&ip="+rowobj['ip']+"' class='btn btn-primary'>设置允许开启服务</a><a href='/monitor/set/valid?is_valid=0&ip="+rowobj['ip']+"' class='btn btn-primary'>设置拒绝开启服务</a>"
          return [
            res
          ].join('');
      }

</script>
%rebase admin_frame_base
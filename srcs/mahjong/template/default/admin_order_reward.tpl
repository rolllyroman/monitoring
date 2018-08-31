<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/refreshDateInit.js"></script>
<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/common.js"></script>
  <div class="block">
            %include admin_frame_header
            <div class="content">
               %include original_search_bar
               <table id="dataTable" class="table table-bordered table-hover"></table>
            </div>
  </div>
<script type="text/javascript">

  function initTable() {
    $('#dataTable').bootstrapTable({
          method: 'get',
          url: '{{info["listUrl"]}}',
          contentType: "application/json",
          datatype: "json",
          cache: false,
          checkboxHeader: true,
          striped: true,
          pagination: true,
          pageSize: 15,
          showExport: true,
          exportTypes:['excel', 'csv', 'pdf', 'json'],
          pageList: [15,50,100,'All'],
          search: true,
          clickToSelect: true,
          //sidePagination : "server",
          sortOrder: 'desc',
          sortName: 'date',
          queryParams:getSearchP,
          responseHandler:responseFun,
          showFooter:true, //添加页脚做统计
          //onLoadError:responseError,
          showExport:true,
          exportTypes:['excel', 'csv', 'pdf', 'json'],
          // exportOptions:{fileName: "{{info['title']}}"+"_"+ new Date().Format("yyyy-MM-dd")},
          columns: [
          {
              field: 'uid',
              title: '玩家id',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'nickname',
              title: '玩家游戏昵称',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'reward_name',
              title: '奖品名称',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'key_code',
              title: '兑换码',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'reward_cost',
              title: '奖品成本',
              align: 'center',
              valign: 'middle',
              sortable:true,
              footerFormatter:function(values){
                 var count = 0;
                 for (var val in values)
                    count+=parseInt(values[val].reward_cost);

                 return '成本合计:'+String(count)
              }
          },{
              field: 'reward_value',
              title: '奖品价格',
              align: 'center',
              valign: 'middle',
              sortable:true,
              footerFormatter:function(values){
                 var count = 0;
                 for (var val in values)
                    count+=parseInt(values[val].reward_value);

                 return '价格合计:'+String(count)
              }
          },{
              field: 'reward_time',
              title: '获取兑换码时间',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'deliver_time',
              title: '发货时间',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'card_no',
              title: '卡号',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'card_pwd',
              title: '卡密',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'cost_type_name',
              title: '消耗类型名称',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'cost_num',
              title: '消耗类型数量',
              align: 'center',
              valign: 'middle',
              sortable:true,
          },{
              field: 'status',
              title: '是否发货',
              align: 'center',
              valign: 'middle',
              sortable: true,
              formatter:is_delivered
          },{
              field: 'op',
              title: '操作',
              align: 'center',
              valign: 'middle',
              formatter:getOp
          }],
          onExpandRow: function (index, row, $detail) {
              console.log(index,row,$detail);
              //InitSubTable(index, row, $detail);
          }
      });


        //定义列操作
        function getSearchP(p){
          startDate = $("#pick-date-start").val();
          endDate   = $("#pick-date-end").val();

          sendParameter = p;

          sendParameter['startDate'] = startDate;
          sendParameter['endDate']  = endDate;

          return sendParameter;
        }

        function getOp(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var a2,a3,a4,a5;
          if(rowobj['is_delete']=='0'){
             a2 = "<a class='btn btn-primary' href='/admin/bag/item/changeI?item_id="+rowobj['reward_code']+"&ci=1'>删除</a>"
          }else{
             a2 = "<a class='btn btn-primary' href='/admin/bag/item/changeI?item_id="+rowobj['reward_code']+"&ci=0'>恢复</a>"
          }

          res = "<a href='/admin/order/reward/edit_deliver?key_code="+rowobj['key_code']+"' class='btn btn-primary'>编辑发货</a>"
          return [
            res
          ].join('');
      }

        function is_delivered(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var statusstr = '';
          if(rowobj['status'] == '0'){
              statusstr = '<span class="label label-danger">未发货</span>';
          }else if(rowobj['status'] == '1'){
              statusstr = '<span class="label label-success">已发货</span>';
          }
          return [
              statusstr
          ].join('');
      }


        //获得返回的json 数据

        function responseFun(res){
            // $('#numberTotal').html(' 销售总个数: <strong style="color:#6600FF">'+res.numberTotal+'</strong>');
            // $('#rateTotal').html('我的总占额: <strong style="color:#6600FF">'+res.rateTotal+'</strong>');
            // $('#superTotal').html('上线总占额: <strong style="color:#6600FF">'+res.superTotal+'</strong>');
            data = res.data
            return data;
        }
}
</script>
%rebase admin_frame_base